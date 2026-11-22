"""Regenerate current publication figures from completed clean CPU scores."""
from pathlib import Path
import csv,json,statistics
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent.parent
VARIANTS=['frozen_whole','whole_lora','peri_lora','fixed_fusion','gated_fusion']
LABELS=['Frozen + projection','Whole LoRA','Periocular LoRA','Fixed fusion','Learned gating']
COLORS=['#0072B2','#E69F00','#009E73','#D55E00','#CC79A7']

def scores(seed,variant,condition):
    path=ROOT/f'results/cpu_clean/evaluation/seed{seed}_{variant}/{condition}_raw_scores.csv'
    with path.open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    return np.array([int(r['label']) for r in rows]),np.array([float(r['score']) for r in rows])

def empirical_roc(y,s):
    order=np.argsort(-s,kind='stable');y=y[order];s=s[order]
    ends=np.r_[np.flatnonzero(np.diff(s)!=0),len(s)-1]
    return np.r_[0,np.cumsum(1-y)[ends]/sum(1-y)],np.r_[0,np.cumsum(y)[ends]/sum(y)]

def save(fig,name):
    for directory in [ROOT/'submission_ieee',ROOT/'submission_arxiv']:
        directory.mkdir(parents=True,exist_ok=True)
        fig.savefig(directory/(name+'.pdf'),bbox_inches='tight',metadata={'CreationDate':None,'ModDate':None})
    plt.close(fig)

def main():
    data=json.loads((ROOT/'results/cpu_clean/RESULTS_SUMMARY.json').read_text())
    assert data['state']=='complete' and data['completed_models']==15
    plt.rcParams.update({'font.size':10,'legend.fontsize':8,'pdf.fonttype':42})
    for c,name,title in [('test_masked','fig_rof_masked_roc','Duplicate-excluded ROF masked; seed 42'),
                         ('test_sunglasses','fig_rof_sunglasses_roc','Duplicate-excluded ROF sunglasses; seed 42'),
                         ('mfr2','fig_mfr2_roc','Known-overlap-excluded MFR2; seed 42')]:
        fig,ax=plt.subplots(figsize=(5.4,4.1))
        for v,label,color in zip(VARIANTS,LABELS,COLORS):
            y,s=scores(42,v,c);f,t=empirical_roc(y,s);keep=f>0
            auc=float(np.sum(np.diff(f)*(t[1:]+t[:-1])/2))
            ax.step(f[keep],t[keep],where='post',label=f'{label} ({auc:.3f})',color=color,lw=1.3)
        neg=int(sum(y==0));ax.set_xscale('log');ax.set_xlim(1/neg,1);ax.set_ylim(0,1.01)
        ax.set(xlabel='Empirical false acceptance rate',ylabel='True acceptance rate',title=title)
        ax.legend(loc='lower right');ax.grid(alpha=.2)
        fig.text(.5,.005,f'Positive FAR only; first nonzero FAR = 1/{neg}. FAR-zero points omitted.',ha='center',fontsize=8)
        fig.tight_layout(rect=[0,.025,1,1]);save(fig,name)
    conditions=['test_masked','test_sunglasses','test_neutral','mfr2','rmfrd']
    fig,ax=plt.subplots(figsize=(6.5,4.1))
    for i,(v,label,color) in enumerate(zip(VARIANTS,LABELS,COLORS)):
        rows=[next(r for r in data['summary'] if r['condition']==c and r['variant']==v) for c in conditions]
        ax.errorbar(np.arange(5)+(i-2)*.10,[r['auc_mean'] for r in rows],yerr=[r['auc_seed_sd'] for r in rows],fmt='o',markersize=4,capsize=3,lw=1,color=color,label=label)
    ax.set_xticks(range(5),['ROF\nmasked','ROF\nsunglasses','ROF\nneutral','MFR2\nretained','RMFRD\nexploratory'])
    ax.set(ylabel='ROC-AUC (mean and seed SD)',ylim=(.65,.99));ax.legend(ncol=2,loc='lower left');ax.grid(axis='y',alpha=.2)
    fig.tight_layout();save(fig,'fig_auc_cross_dataset')
    y,s=scores(42,'gated_fusion','test_masked');bins=np.linspace(s.min(),s.max(),26)
    fig,ax=plt.subplots(figsize=(5.4,3.6))
    for cls,label,color in [(0,'Impostor','#D55E00'),(1,'Genuine','#009E73')]:
        ax.hist(s[y==cls],bins=bins,density=True,alpha=.5,label=f'{label} (n={sum(y==cls)})',color=color)
    ax.set(xlabel='Cosine score',ylabel='Within-class density',title='New ROF masked gated scores; seed 42')
    ax.legend();ax.grid(alpha=.15);fig.tight_layout();save(fig,'fig_rof_masked_scores')
    print('Regenerated five vector figures from completed CPU results.')

if __name__=='__main__':main()
