import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arabic_qa.checks import run_checks, script_stats
from arabic_qa.dialect import guess_dialect
from arabic_qa.normalize import fold_digits, normalize, strip_tatweel


class TestChecks(unittest.TestCase):
    def test_clean_msa(self):
        self.assertEqual(run_checks("القاهرة هي عاصمة مصر وأكبر مدنها."), [])

    def test_mojibake_is_error(self):
        findings = run_checks("Ø§Ù„Ù‚Ø§Ù‡Ø±Ø©")
        self.assertTrue(any(f.check == "mojibake" and f.severity == "error"
                            for f in findings))

    def test_mixed_digits_warns(self):
        findings = run_checks("الطول ٦٦٥٠ كم والعرض 40 كم")
        self.assertTrue(any(f.check == "mixed_digits" for f in findings))

    def test_tatweel_warns(self):
        findings = run_checks("أهـــلاً بـــكم")
        self.assertTrue(any(f.check == "tatweel" for f in findings))

    def test_code_switch_respects_expected(self):
        text = "ابعتلي الـ email بتاع العميل"
        self.assertTrue(any(f.check == "code_switch"
                            for f in run_checks(text, expected="ar")))
        self.assertFalse(any(f.check == "code_switch"
                             for f in run_checks(text, expected="mixed")))


class TestDialect(unittest.TestCase):
    def test_egyptian(self):
        g = guess_dialect("عايز أروح السينما بكرة، إيه رأيك؟ الجو كده حلو")
        self.assertEqual(g.variety, "egyptian")
        self.assertIn(g.confidence, ("medium", "high"))

    def test_levantine(self):
        g = guess_dialect("شو بدك تعمل هلق؟ ليش ما رحت منيح؟")
        self.assertEqual(g.variety, "levantine")

    def test_msa(self):
        g = guess_dialect("إن التقرير الذي أعده الفريق يتضمن تحليلًا شاملًا، حيث قدم نتائج دقيقة")
        self.assertEqual(g.variety, "msa")

    def test_unknown(self):
        self.assertEqual(guess_dialect("hello world").variety, "unknown")


class TestNormalize(unittest.TestCase):
    def test_fold_digits(self):
        self.assertEqual(fold_digits("٦٦٥٠"), "6650")

    def test_strip_tatweel(self):
        self.assertEqual(strip_tatweel("أهــلا"), "أهلا")

    def test_alef_unification(self):
        self.assertEqual(normalize("أإآ"), "ااا")

    def test_diacritics_stripped(self):
        self.assertEqual(normalize("السَّلَامُ عَلَيْكُمْ"), "السلام عليكم")

    def test_ya_opt_in(self):
        self.assertEqual(normalize("على", ya=True), "علي")
        self.assertEqual(normalize("على"), "على")  # default keeps alef-maqsura


class TestScriptStats(unittest.TestCase):
    def test_ratio(self):
        s = script_stats("القاهرة Cairo")
        self.assertAlmostEqual(s["arabic_ratio"], 0.583, places=2)


if __name__ == "__main__":
    unittest.main()
