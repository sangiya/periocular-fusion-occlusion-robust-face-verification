"""Standard-library regression checks for metric validity and unsafe input rejection."""
from pathlib import Path,PurePosixPath
import ast,csv,importlib.util,os,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"code"))
from verify_results import score_metrics,align,recorded_relative_path,digest

class ArtifactGuards(unittest.TestCase):
    def test_recorded_paths_accept_both_separator_styles_on_any_host(self):
        expected=PurePosixPath('evaluation/seed7_gated_fusion/EVALUATION_REPORT.json')
        for path in ['cpu_runs/evaluation/seed7_gated_fusion/EVALUATION_REPORT.json',
                     r'cpu_runs\evaluation\seed7_gated_fusion\EVALUATION_REPORT.json',
                     r'cpu_runs\\evaluation\\seed7_gated_fusion\\EVALUATION_REPORT.json',
                     r'cpu_runs/evaluation\seed7_gated_fusion/EVALUATION_REPORT.json']:
            with self.subTest(path=path):
                self.assertEqual(recorded_relative_path(path,prefix='cpu_runs'),expected)
        self.assertEqual(recorded_relative_path(r'document\BUILD_REPORT.json'),PurePosixPath('document/BUILD_REPORT.json'))

    def test_recorded_paths_reject_outside_release_and_wrong_prefix(self):
        for path in ['', '.', '../outside.json', r'cpu_runs\..\outside.json',
                     '/tmp/outside.json',r'C:\outside.json',r'C:outside.json',
                     r'\\server\share\outside.json',r'\outside.json','bad\x00path']:
            with self.subTest(path=path),self.assertRaises(ValueError):recorded_relative_path(path)
        for path in ['elsewhere/report.json','cpu_runs_other/report.json','cpu_runs']:
            with self.subTest(path=path),self.assertRaises(ValueError):recorded_relative_path(path,prefix='cpu_runs')

    def test_actual_historical_report_paths_resolve_and_keep_hashes(self):
        import json
        base=ROOT/'results/cpu_clean'
        reports=json.loads((base/'RESULTS_SUMMARY.json').read_text())['evaluation_report_hashes']
        self.assertEqual(len(reports),15)
        for path,expected in reports.items():
            relative=recorded_relative_path(path,prefix='cpu_runs')
            self.assertEqual(relative.parts[0],'evaluation')
            self.assertEqual(digest(base/relative),expected)

    def test_perfect_and_reversed_scores(self):
        good=[{"score":s,"label":y} for s,y in [(.9,1),(.8,1),(.2,0),(.1,0)]]
        self.assertEqual(score_metrics(good)["auc"],1)
        self.assertEqual(score_metrics(good)["eer"],0)
        reverse=[{"score":-r["score"],"label":r["label"]} for r in good]
        self.assertEqual(score_metrics(reverse)["auc"],0)
    def test_ties(self):
        tied=[{"score":s,"label":y} for s,y in [(.9,1),(.9,0),(.1,1),(.1,0)]]
        self.assertAlmostEqual(score_metrics(tied)["auc"],.5)
        self.assertAlmostEqual(score_metrics(tied)["eer"],.5)
    def test_invalid_scores_and_labels_are_errors(self):
        for rs in [[],[{"score":float("nan"),"label":0},{"score":.2,"label":1}],
                   [{"score":.5,"label":2},{"score":.2,"label":1}],
                   [{"score":.5,"label":1}]]:
            with self.subTest(rows=rs),self.assertRaises(ValueError):score_metrics(rs)
    def test_pair_id_mismatch_is_error(self):
        with self.assertRaises(ValueError):
            align([{"label":"1","pair_id":"wrong"}],[{"label":"1","pair_id":"actual"}])
    def test_archived_training_input_is_rejected_before_loading_images(self):
        tree=ast.parse((ROOT/"code/train.py").read_text(encoding="utf-8"))
        fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="read_rows")
        namespace={"Path":Path,"csv":csv}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),"<trainer input guard>","exec"),namespace)
        with self.assertRaisesRegex(ValueError,"content-unique"):
            namespace["read_rows"](ROOT/"manifests/crop_manifest_training_person_disjoint.csv")
    def test_clean_manifest_has_unique_content_and_no_label_split_overlap(self):
        with (ROOT/"manifests/cleaned/rof_training_clean.csv").open(encoding="utf-8") as f:rs=list(csv.DictReader(f))
        self.assertEqual(len(rs),len({r["sha256"] for r in rs}))
        ids={}
        for r in rs:ids.setdefault(r["identity"],set()).add(r["split"])
        self.assertTrue(all(len(x)==1 for x in ids.values()))
if __name__=="__main__":unittest.main()

