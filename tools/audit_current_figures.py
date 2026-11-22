"""Check the current figure inputs independently and bind the actual PDF bytes."""
from pathlib import Path
import csv, hashlib, importlib.util, io, json, sys
import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve

ROOT = Path(__file__).resolve().parent.parent

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    spec = importlib.util.spec_from_file_location('current_figures', ROOT/'code/regenerate_completed_assets.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    summary = json.loads((ROOT/'results/cpu_clean/RESULTS_SUMMARY.json').read_text())
    checked = []
    for folder in sorted((ROOT/'results/cpu_clean/evaluation').iterdir()):
        if not folder.is_dir():
            continue
        report = json.loads((folder/'EVALUATION_REPORT.json').read_text())
        for condition, item in report['protocols'].items():
            path = folder/item['raw_scores']
            with path.open(encoding='utf-8', newline='') as handle:
                rows = list(csv.DictReader(handle))
            labels = np.array([int(row['label']) for row in rows])
            scores = np.array([float(row['score']) for row in rows])
            assert np.isfinite(scores).all() and set(labels) == {0, 1}
            auc = float(roc_auc_score(labels, scores))
            assert abs(auc-item['metrics']['auc']) < 1e-12, str(path)
            checked.append({'file':path.relative_to(ROOT).as_posix(), 'sha256':sha(path.read_bytes()), 'auc':auc})
    figures = []
    conditions = {'fig_rof_masked_roc':'test_masked', 'fig_rof_sunglasses_roc':'test_sunglasses', 'fig_mfr2_roc':'mfr2'}
    def inspect(fig, name):
        ax = fig.axes[0]
        if name in conditions:
            condition = conditions[name]
            for line, variant, label in zip(ax.lines, module.VARIANTS, module.LABELS):
                y, s = module.scores(42, variant, condition)
                fpr, tpr, _ = roc_curve(y, s, drop_intermediate=False)
                positive = fpr > 0
                np.testing.assert_allclose(line.get_xdata(), fpr[positive], atol=1e-14)
                np.testing.assert_allclose(line.get_ydata(), tpr[positive], atol=1e-14)
                assert line.get_label() == f'{label} ({roc_auc_score(y,s):.3f})'
            assert len(ax.lines) == 5 and ax.get_xscale() == 'log'
        elif name == 'fig_auc_cross_dataset':
            conditions_order = ['test_masked','test_sunglasses','test_neutral','mfr2','rmfrd']
            for container, variant in zip(ax.containers, module.VARIANTS):
                line, caps, bars = container.lines
                rows = [next(row for row in summary['summary'] if row['condition']==c and row['variant']==variant) for c in conditions_order]
                means = np.array([row['auc_mean'] for row in rows])
                sd = np.array([row['auc_seed_sd'] for row in rows])
                np.testing.assert_allclose(np.asarray(line.get_ydata(),dtype=float), means)
                segments = bars[0].get_segments()
                np.testing.assert_allclose([segment[:,1] for segment in segments], np.c_[means-sd,means+sd])
        else:
            assert name == 'fig_rof_masked_scores'
            y, scores = module.scores(42,'gated_fusion','test_masked')
            bins = np.linspace(scores.min(),scores.max(),26)
            assert len(ax.patches) == 50
            for i, label in enumerate([0,1]):
                heights, _ = np.histogram(scores[y==label], bins=bins, density=True)
                np.testing.assert_allclose([patch.get_height() for patch in ax.patches[i*25:(i+1)*25]],heights)
                assert abs(np.sum(heights*np.diff(bins))-1) < 1e-12
        buffer = io.BytesIO()
        fig.savefig(buffer,format='pdf',bbox_inches='tight',metadata={'CreationDate':None,'ModDate':None})
        current = ROOT/'submission_ieee'/(name+'.pdf')
        assert buffer.getvalue() == current.read_bytes(), 'Figure differs from current generator: '+name
        assert current.read_bytes() == (ROOT/'submission_arxiv'/current.name).read_bytes()
        figures.append({'file':current.relative_to(ROOT).as_posix(),'sha256':sha(current.read_bytes()),'recreated_pdf_byte_identical':True})
        module.plt.close(fig)
    module.save = inspect
    module.main()
    output = {'date':'2026-11-22','status':'passed','independent_auc_library':'scikit-learn',
              'raw_score_files':checked,'figures':figures,
              'scope':'Independent library AUC/ROC checks; plotted means/error bars and histogram inputs; exact regenerated PDF bytes. Does not validate semantic image labels, unseen identities, or repeat neural inference.'}
    (ROOT/'document/FIGURE_DATA_AUDIT.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(f'Independent AUC checks: {len(checked)} files; current vector figures: {len(figures)} byte-identical and data-checked.')

if __name__ == '__main__':
    main()
