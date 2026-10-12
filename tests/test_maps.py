import hashlib
import json
import pickle
import random
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pathfinding_emulator.config import SAMPLE_MAPS_DIR
from pathfinding_emulator.environment import base_map
from pathfinding_emulator.maps import ChallengeDesigner, load_map


class MapsTests(unittest.TestCase):
    def test_all_original_maps_load(self):
        samples = list(SAMPLE_MAPS_DIR.glob("*.pickle"))
        self.assertEqual(len(samples), 14)
        for path in samples:
            with self.subTest(path=path):
                grid = load_map(path)
                self.assertTrue(grid)
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                    json.loads(
                        (
                            Path(__file__).parent / "fixtures/sample_map_hashes.json"
                        ).read_text()
                    )[path.name],
                )

    def test_json_round_trip_and_exclusive_concurrent_saves(self):
        with tempfile.TemporaryDirectory() as directory:
            designer = ChallengeDesigner(directory)
            grid = base_map(2, 3)
            grid[1][1] = 1
            with ThreadPoolExecutor(max_workers=4) as pool:
                paths = list(pool.map(designer.save_map, [grid] * 8))
            self.assertEqual(len(set(paths)), 8)
            for path in paths:
                self.assertEqual(load_map(path), grid)
                self.assertEqual(Path(path).suffix, ".json")

    def test_legacy_windows_and_extensionless_paths(self):
        designer = ChallengeDesigner()
        self.assertEqual(
            designer.load_map(r"maps\map_7"), load_map(SAMPLE_MAPS_DIR / "map_7.json")
        )
        self.assertEqual(
            designer.load_map(r"maps\map_7.pickle"),
            load_map(SAMPLE_MAPS_DIR / "map_7.pickle"),
        )
        with self.assertRaises(FileNotFoundError):
            designer.load_map("/missing/custom/map_7")

    def test_malicious_pickle_rejected_without_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "executed"

            class Payload:
                def __reduce__(self):
                    return eval, (f"open({str(marker)!r}, 'w').write('unsafe')",)

            path = Path(directory) / "evil.pickle"
            path.write_bytes(pickle.dumps(Payload()))
            with self.assertRaisesRegex(ValueError, "unsafe"):
                load_map(path)
            self.assertFalse(marker.exists())

    def test_cyclic_and_malformed_input(self):
        with tempfile.TemporaryDirectory() as directory:
            for content, suffix in (
                (b"not json", ".json"),
                (b"broken", ".pickle"),
                (b"x" * (1024 * 1024 + 1), ".json"),
            ):
                path = Path(directory) / ("map" + suffix)
                path.write_bytes(content)
                with self.assertRaises(ValueError):
                    load_map(path)
            cyclic = []
            cyclic.append(cyclic)
            path = Path(directory) / "cycle.pickle"
            path.write_bytes(pickle.dumps(cyclic))
            with self.assertRaises(ValueError):
                load_map(path)

    def test_huge_pickle_memo_index_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memo.pickle"
            path.write_bytes(b"\x80\x03]r\xff\xff\xff\xff.")
            with self.assertRaisesRegex(ValueError, "memo reference"):
                load_map(path)

    def test_seeded_generation_dimensions_and_counts(self):
        for height, width in ((1, 1), (2, 2), (3, 7), (7, 3), (10, 10)):
            for seed in range(20):
                with self.subTest(size=(height, width), seed=seed):
                    a = ChallengeDesigner(rng=random.Random(seed))
                    b = ChallengeDesigner(rng=random.Random(seed))
                    a.create_random_map(1, 1, height, width)
                    b.create_random_map(1, 1, height, width)
                    self.assertEqual(a.mapArr, b.mapArr)
                    self.assertEqual(
                        (len(a.mapArr), len(a.mapArr[0])), (height + 2, width + 2)
                    )
                    self.assertEqual(
                        sum(row.count(1) for row in a.mapArr), int(0.5 * height * width)
                    )
