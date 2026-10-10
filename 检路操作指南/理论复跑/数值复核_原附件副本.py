"""检路方案数值复核  本代码用于理论论证 不替代Proteus工程或MCU程序。"""
import csv
import itertools
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'audit'
OUT.mkdir(exist_ok=True)
RS = 2000.0
VREF = 3.3
LSB = VREF / 4095
ANALOG_ERROR = 0.003
# A single conservative LUT covers either a 10-bit or 12-bit ADC API return.
# The real API range still has to be measured and normalized by A.
TOTAL_ERROR = 0.005
TB, TA, JITTER = .050, .055, .001
N = 5000
RNG = np.random.default_rng(20261010)


def cases(kind):
    if kind == 'DIV':
        return [('正常',10000,10000),('R1断路',10000,10000),
                ('R2断路',10000,10000),('R1短路',10000,10000),
                ('R2短路',10000,10000),('R1为5kΩ',5000,10000),
                ('R1为20kΩ',20000,10000),('R2为5kΩ',10000,5000),
                ('R2为20kΩ',10000,20000)]
    return [('正常',10000,10e-6),('R断路',10000,10e-6),
            ('C断路',10000,10e-6),('R短路',10000,10e-6),
            ('C短路',10000,10e-6),('R为5kΩ',5000,10e-6),
            ('R为20kΩ',20000,10e-6),('C为5μF',10000,5e-6),
            ('C为20μF',10000,20e-6)]


def features(kind, fault, vs, rs, x, y, tb=TB, ta=TA):
    """返回列顺序VB VA；开路边界按高阻ADC和RC已放电的理想等效模型计算。"""
    if kind == 'DIV':
        r1, r2 = x, y
        if fault == 'R1断路': return np.stack((np.zeros_like(vs),vs),-1)
        if fault == 'R2断路': return np.stack((vs,vs),-1)
        if fault == 'R1短路': r1 = np.zeros_like(r1)
        if fault == 'R2短路': r2 = np.zeros_like(r2)
        den = rs+r1+r2
        return np.stack((vs*r2/den,vs*(r1+r2)/den),-1)
    r, c = x, y
    if fault == 'R断路': return np.stack((np.zeros_like(vs),vs),-1)
    if fault == 'C断路': return np.stack((vs,vs),-1)
    if fault == 'C短路': return np.stack((np.zeros_like(vs),vs*r/(rs+r)),-1)
    if fault == 'R短路': r=np.zeros_like(r)
    tau=(rs+r)*c
    return np.stack((vs*(1-np.exp(-tb/tau)),vs*(1-rs/(rs+r)*np.exp(-ta/tau))),-1)


def classify(values_mv, bounds_mv, mode='adaptive'):
    one=(values_mv[:,None,0]>=bounds_mv[None,:,0,0])&(values_mv[:,None,0]<=bounds_mv[None,:,0,1])
    n=one.sum(1)
    if mode=='fixed': use2=np.ones(len(n),dtype=bool)
    else: use2=(n>1)|((n==1)&one[:,0])
    two=one&(values_mv[:,None,1]>=bounds_mv[None,:,1,0])&(values_mv[:,None,1]<=bounds_mv[None,:,1,1])
    match=np.where(use2[:,None],two,one)
    counts=match.sum(1)
    pred=np.where(counts==1,match.argmax(1),-1)
    return pred,1+use2.astype(int)


def measured_mv(v, bits=12, noise=None):
    # ±3 mV analog/reconstruction error followed by 12-bit quantization and integer-mV storage.
    shifted=np.clip(v+(RNG.uniform(-ANALOG_ERROR,ANALOG_ERROR,v.shape) if noise is None else noise),0,VREF)
    step=VREF/(2**bits-1)
    return np.rint(np.rint(shifted/step)*step*1000).astype(int)


report={'version':'2.0','assumptions':{
    'source_V':1.0,'source_tolerance':.01,'Rs_ohm':RS,'Rs_tolerance':.01,
    'R_tolerance':.05,'C_tolerance':.10,'C_normal_F':10e-6,
    'sample_VB_s':TB,'sample_VA_s':TA,'timing_jitter_s':JITTER,
    'analog_reconstruction_error_V':ANALOG_ERROR,'adc_reference_V':VREF,
    'adc_bits':12,'adc_step_mV':LSB*1000,'lut_total_envelope_mV':TOTAL_ERROR*1000,
    'checked_api_bits':[10,12],'samples_per_state':N,'seed':20261010},
    'templates':{}}
lut_rows=[]
test_rows=[]
for kind in ('DIV','RC'):
    states=[]
    bounds=[]
    for idx,(name,x0,y0) in enumerate(cases(kind)):
        ytol=.05 if kind=='DIV' else .10
        params=np.array(list(itertools.product((.99,1.01),(RS*.99,RS*1.01),
             (x0*.95,x0*1.05),(y0*(1-ytol),y0*(1+ytol)),
             (TB-JITTER,TB+JITTER),(TA-JITTER,TA+JITTER))))
        v=features(kind,name,*[params[:,i] for i in range(6)])
        b=np.stack((np.floor((v.min(0)-TOTAL_ERROR)*1000),np.ceil((v.max(0)+TOTAL_ERROR)*1000)),-1).astype(int)
        bounds.append(b)
        nom=features(kind,name,np.array([1.]),np.array([RS]),np.array([x0]),np.array([y0]))[0]
        states.append({'id':f'{kind}{idx}','name':name,'x_ohm':x0,'y_ohm_or_F':y0,'nominal_VB_mV':float(nom[0]*1000),'nominal_VA_mV':float(nom[1]*1000),'bounds_mV':b.tolist()})
        lut_rows.append([f'{kind}{idx}',kind,name,x0,y0,TB*1000 if kind=='RC' else '稳态',TA*1000 if kind=='RC' else '稳态',*b[0],*b[1],round(nom[0]*1000,3),round(nom[1]*1000,3)])
        test_rows.append([f'{kind}{idx}',kind,name,x0,y0,round(nom[0]*1000,3),round(nom[1]*1000,3)]+['']*9)
    bounds=np.array(bounds)
    # Check every pair of rounded feature rectangles, rather than trusting random samples alone.
    overlaps=[]
    min_pair_gap=np.inf
    for i,j in itertools.combinations(range(9),2):
        gap=np.maximum(bounds[i,:,0]-bounds[j,:,1],bounds[j,:,0]-bounds[i,:,1])
        if np.all(gap<=0): overlaps.append([states[i]['id'],states[j]['id']])
        min_pair_gap=min(min_pair_gap,float(np.max(gap)))
    assert not overlaps,(kind,overlaps)
    tests=[]
    tests10=[]
    healthy_windows=[]
    for idx,(name,x0,y0) in enumerate(cases(kind)):
        yt=.05 if kind=='DIV' else .10
        inputs=[RNG.uniform(.99,1.01,N),RNG.uniform(RS*.99,RS*1.01,N),
                RNG.uniform(x0*.95,x0*1.05,N),RNG.uniform(y0*(1-yt),y0*(1+yt),N),
                RNG.uniform(TB-JITTER,TB+JITTER,N),RNG.uniform(TA-JITTER,TA+JITTER,N)]
        base=features(kind,name,*inputs)
        noise=RNG.uniform(-ANALOG_ERROR,ANALOG_ERROR,base.shape)
        values=measured_mv(base,12,noise)
        pred,reads=classify(values,bounds)
        fixed,fixed_reads=classify(values,bounds,'fixed')
        assert np.all(pred==idx) and np.all(fixed==idx),(kind,name)
        tests.append({'id':f'{kind}{idx}','samples':N,'correct':int((pred==idx).sum()),'wrong':int(((pred>=0)&(pred!=idx)).sum()),'unknown_or_ambiguous':int((pred<0).sum()),'feature_reads':int(reads.sum())})
        vals10=measured_mv(base,10,noise)
        pred10,reads10=classify(vals10,bounds)
        assert np.all(pred10==idx),(kind,name,'10-bit API case')
        tests10.append({'id':f'{kind}{idx}','samples':N,'correct':int((pred10==idx).sum()),'feature_reads':int(reads10.sum())})
        if idx==0:
            nom=np.array([states[0]['nominal_VB_mV'],states[0]['nominal_VA_mV']])
            for percent in (1,3,5,10):
                half=np.maximum(3.5,np.abs(nom)*percent/100)
                alarm=(np.abs(values-nom)>half).any(1)
                healthy_windows.append({'nominal_window_percent':percent,'normal_false_alarm_samples':int(alarm.sum()),'samples':N})
    total=N*9; reads=sum(x['feature_reads'] for x in tests)
    report['templates'][kind]={'states':states,'pairwise_rectangle_overlaps':overlaps,
       'minimum_pair_separation_mV':min_pair_gap,'test_counts':tests,
       'normal_threshold_sweep':healthy_windows,'10bit_api_checks':tests10,'10bit_aggregate':{
       'samples':total,'correct':sum(x['correct'] for x in tests10),'mean_feature_reads':sum(x['feature_reads'] for x in tests10)/total,
       'feature_read_reduction':1-sum(x['feature_reads'] for x in tests10)/(total*2)},'aggregate':{
       'samples':total,'correct':sum(x['correct'] for x in tests),'mean_feature_reads':reads/total,
       'feature_read_reduction':1-reads/(total*2)}}

unknown=[]
for r in (12000.,20000.):
    vals=features('DIV','正常',np.array([1.]),np.array([RS]),np.array([r]),np.array([r]))
    b=np.array([x['bounds_mV'] for x in report['templates']['DIV']['states']])
    obs=np.rint(vals*1000).astype(int)
    pred,reads=classify(obs,b)
    unknown.append({'R1_ohm':r,'R2_ohm':r,'VB_mV':int(obs[0,0]),'VA_mV':int(obs[0,1]),'prediction':int(pred[0]),'feature_reads':int(reads[0])})
report['out_of_library_examples']=unknown
report['scope']='只验证两个指定拓扑的预设单故障；模型外复合参数可能落入正常特征区间。'
(OUT/'理论复核结果.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'特征区间_v2.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.writer(f);writer.writerow(['状态编号','模板','状态','R1或R_Ω','R2_Ω或C_F','VB采样_ms','VA采样_ms','VB下界_mV','VB上界_mV','VA下界_mV','VA上界_mV','标称VB_mV','标称VA_mV']);writer.writerows(lut_rows)
with (OUT/'仿真记录_18工况.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.writer(f);writer.writerow(['状态编号','模板','故障设置','R1或R_Ω','R2_Ω或C_F','理论VB_mV','理论VA_mV','实测VB_mV','实测VA_mV','实际判别','运行供电状态','判别特征次数','全部ADC转换次数','总耗时_ms','截图编号','备注']);writer.writerows(test_rows)
print(json.dumps({k:v['aggregate']|{'区间重叠对数':len(v['pairwise_rectangle_overlaps']),'最小区分间隔_mV':v['minimum_pair_separation_mV']} for k,v in report['templates'].items()},ensure_ascii=False,indent=2))
print('模型外示例',json.dumps(unknown,ensure_ascii=False))
