"""Draw a vector explanation of the executed gated-fusion inference path."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
ROOT=Path(__file__).resolve().parent.parent
def main():
    fig,ax=plt.subplots(figsize=(10,5.2));ax.set_xlim(0,10);ax.set_ylim(0,5.2);ax.axis('off')
    def box(x,y,w,h,text,color='#e8f1f8'):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.04',fc=color,ec='#34556a',lw=1))
        ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=10)
    def arrow(a,b):ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=12,color='#34556a',lw=1.15))
    box(.15,3.55,1.4,.65,'Whole-face\ncrop')
    box(.15,2.25,1.4,.65,'Periocular\ncrop')
    box(2,3.55,2.1,.65,'DINOv2 + LoRA\nprojection + norm')
    box(2,2.25,2.1,.65,'DINOv2 + LoRA\nprojection + norm')
    box(4.55,3.55,1,.65,'Face\nembedding')
    box(4.55,2.25,1,.65,'Periocular\nembedding')
    box(4.05,.65,2.1,.8,'Constant auxiliary input\n[1, 0, 0, 1]','#f2f2f2')
    box(6.4,2.9,1.3,1.05,'Embedding-\nconditioned\ngate: g','#fff2d7')
    box(8.15,2.6,1.6,1.65,'Normalize\ng z(face) +\n(1 - g) z(peri)','#e6f3e9')
    arrow((1.6,3.87),(1.97,3.87));arrow((1.6,2.57),(1.97,2.57))
    arrow((4.13,3.87),(4.52,3.87));arrow((4.13,2.57),(4.52,2.57))
    arrow((5.58,3.87),(6.37,3.65));arrow((5.58,2.57),(6.37,3.16))
    arrow((6.15,1.1),(6.95,2.87));arrow((7.73,3.43),(8.12,3.43))
    arrow((5.05,4.23),(8.93,4.28));arrow((5.58,2.57),(8.12,2.78))
    arrow((8.95,2.57),(8.95,1.52))
    ax.text(8.95,1.25,'Unit embedding',ha='center',fontsize=10,fontweight='bold')
    ax.text(8.95,.8,'Cosine comparison\nwith enrollment embedding',ha='center',va='top',fontsize=9)
    ax.text(.15,4.85,'Gated fusion (M4): inference for one image',fontsize=13,fontweight='bold')
    ax.text(.15,.12,'The auxiliary vector is fixed; it supplies no measured image-specific quality variation.',fontsize=10)
    fig.tight_layout(pad=.3)
    out=ROOT/'document/thesis';out.mkdir(exist_ok=True)
    fig.savefig(out/'fig_gated_architecture.pdf',bbox_inches='tight',metadata={'CreationDate':None,'ModDate':None})
    fig.savefig(out/'fig_gated_architecture.png',bbox_inches='tight',dpi=180)
    print('Saved vector method diagram for the thesis.')
if __name__=='__main__':main()
