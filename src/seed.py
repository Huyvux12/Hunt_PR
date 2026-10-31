from src.database import init_db, save_issue
from src.generator import generate_static_data

init_db()

demo_issues = [
    {
        'id': 1001,
        'repo_name': 'datamodel-code-generator/datamodel-code-generator',
        'repo_stars': 4047,
        'repo_url': 'https://github.com/datamodel-code-generator/datamodel-code-generator',
        'issue_number': 5754,
        'title': "The agent skill's first command, uvx datamodel-codegen --help, fails because no package of that name exists",
        'body': "When running `uvx datamodel-codegen --help`, it raises error because the package name on PyPI is `datamodel-code-generator`.\n\nSteps to reproduce:\n```bash\nuvx datamodel-codegen --help\n```",
        'html_url': 'https://github.com/datamodel-code-generator/datamodel-code-generator/issues/5754',
        'comments_count': 0,
        'labels': ['bug', 'documentation', 'good first issue'],
        'language': 'Python',
        'created_at': '2026-10-31T05:00:00Z',
        'updated_at': '2026-10-31T05:10:00Z',
        'merge_velocity_hours': 0.6,
        'merge_verdict': '🔥 CỰC DỄ (TB 0.6h là merge)',
        'agent_score': 95,
        'has_code_block': True
    },
    {
        'id': 1002,
        'repo_name': 'datamodel-code-generator/datamodel-code-generator',
        'repo_stars': 4047,
        'repo_url': 'https://github.com/datamodel-code-generator/datamodel-code-generator',
        'issue_number': 5748,
        'title': 'A client resource or server router named after a tag that is not in NFKC form cannot be imported',
        'body': "Unicode normalization issue in identifiers:\n```python\nfrom unicodedata import normalize\n```",
        'html_url': 'https://github.com/datamodel-code-generator/datamodel-code-generator/issues/5748',
        'comments_count': 1,
        'labels': ['bug', 'good first issue'],
        'language': 'Python',
        'created_at': '2026-10-31T04:00:00Z',
        'updated_at': '2026-10-31T04:30:00Z',
        'merge_velocity_hours': 0.6,
        'merge_verdict': '🔥 CỰC DỄ (TB 0.6h là merge)',
        'agent_score': 90,
        'has_code_block': True
    },
    {
        'id': 1003,
        'repo_name': 'tile-ai/tilelang',
        'repo_stars': 8860,
        'repo_url': 'https://github.com/tile-ai/tilelang',
        'issue_number': 3721,
        'title': '[Bug][CUDA][Fuzz] T.gemm on TMEM emits no tcgen05.mma when threads / 32 does not divide N: the product is silently lost',
        'body': 'In TileLang, CUDA compilation misses code generation when thread count does not match partition.',
        'html_url': 'https://github.com/tile-ai/tilelang/issues/3721',
        'comments_count': 1,
        'labels': ['bug', 'cuda'],
        'language': 'Python',
        'created_at': '2026-10-30T10:00:00Z',
        'updated_at': '2026-10-31T03:00:00Z',
        'merge_velocity_hours': 350.0,
        'merge_verdict': '⚠️ TRUNG BÌNH (TB 14.6 ngày)',
        'agent_score': 75,
        'has_code_block': True
    }
]

for d in demo_issues:
    save_issue(d)

generate_static_data()
print("Initial seed completed!")
