"""Protocol unit tests; these do not demonstrate actual robot navigation."""
import sys
from pathlib import Path
import unittest
import tempfile
import yaml
from unittest.mock import Mock, patch
from builtin_interfaces.msg import Time
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from navigation_node import NavigationNode, TaskResult, load_goals


class NavigationProtocolTest(unittest.TestCase):
    def test_unset_goals(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as stream:
            yaml.safe_dump({'goals': [dict(x=None, y=None, yaw=None)] * 3}, stream)
            stream.flush()
            with self.assertRaisesRegex(ValueError, 'unset/invalid'):
                load_goals(stream.name)

    def test_stops_at_failure(self):
        fake = Mock()
        fake.get_parameter.side_effect = lambda key: type('P', (), {
            'value': 'unused' if key == 'goals_file' else 10.0})()
        fake.get_clock().now().to_msg.return_value = Time()
        fake.isTaskComplete.return_value = True
        fake.getResult.side_effect = [TaskResult.SUCCEEDED, TaskResult.FAILED]
        with patch('navigation_node.load_goals', return_value=[dict(x=0, y=0, yaw=0)] * 3):
            with self.assertRaisesRegex(RuntimeError, 'Goal 2 failed'):
                NavigationNode.run(fake)
        self.assertEqual(fake.goToPose.call_count, 2)
        self.assertFalse(any('All navigation goals' in str(c) for c in fake.info.call_args_list))


if __name__ == '__main__':
    unittest.main()
