"""Refresh public GitHub cards; no private repository or account data is fetched."""
from pathlib import Path
import os, json, urllib.request, html, textwrap

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
ASSETS.mkdir(exist_ok=True)
HEADERS = {'User-Agent': 'Veydr-public-profile', 'Accept': 'application/vnd.github+json'}
if os.environ.get('GITHUB_TOKEN'):
    HEADERS['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']

def fetch(path):
    request = urllib.request.Request('https://api.github.com/' + path, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)

def start(width, height):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><style>text{{font-family:Segoe UI,Arial,sans-serif}}.mono{{font-family:Consolas,monospace}}.pulse{{animation:pulse 4s ease-in-out infinite}}@keyframes pulse{{50%{{opacity:.35}}}}@media(prefers-reduced-motion:reduce){{.pulse{{animation:none}}}}</style><rect x="1" y="1" width="{width-2}" height="{height-2}" rx="16" fill="#07131f" stroke="#204657"/>'''

profile = fetch('users/Veydr')
repos = []
for page in range(1, 11):
    batch = fetch(f'users/Veydr/repos?type=owner&per_page=100&page={page}')
    repos.extend(batch)
    if len(batch) < 100:
        break
pulls = fetch('search/issues?q=author%3AVeydr+is%3Apr+is%3Apublic&sort=created&per_page=5')

stats = [('PUBLIC REPOS', profile['public_repos']), ('FOLLOWERS', profile['followers']),
         ('REPO STARS', sum(r['stargazers_count'] for r in repos)), ('PUBLIC PRs', pulls['total_count'])]
svg = start(1520, 215)
svg += '<text x="28" y="35" fill="#64dff4" font-size="15" class="mono" letter-spacing="2">PUBLIC GITHUB SNAPSHOT</text>'
for i, (label, value) in enumerate(stats):
    x = 30 + i * 375
    if i:
        svg += f'<path d="M{x-20} 65V177" stroke="#204657"/>'
    svg += f'<text x="{x}" y="119" fill="#f0fbff" font-size="51" font-weight="700">{value}</text><text x="{x}" y="156" fill="#91abba" font-size="16" class="mono" letter-spacing="1">{label}</text>'
svg += '<circle class="pulse" cx="1478" cy="31" r="5" fill="#3bdbff"/></svg>'
(ASSETS / 'github-stats.svg').write_text(svg, encoding='utf-8', newline='\n')

items = pulls.get('items', [])
height = max(170, 82 + len(items) * 98)
svg = start(1520, height)
svg += '<text x="28" y="36" fill="#64dff4" font-size="16" class="mono" letter-spacing="2">RECENT PUBLIC PULL REQUESTS</text>'
for i, item in enumerate(items):
    y = 86 + i * 98
    repository = item['repository_url'].split('/repos/')[-1]
    state = 'OPEN' if item['state'] == 'open' else 'CLOSED'
    title = textwrap.shorten(item['title'], width=87, placeholder='…')
    svg += f'<circle cx="34" cy="{y-6}" r="4" fill="#3bdbff"/><text x="54" y="{y}" fill="#edf8ff" font-size="23">{html.escape(title)}</text>'
    svg += f'<text x="54" y="{y+31}" fill="#91abba" font-size="17" class="mono">{html.escape(repository)}  /  #{item["number"]}  /  {state}</text>'
if not items:
    svg += '<text x="28" y="104" fill="#91abba" font-size="23">No public pull requests available.</text>'
svg += '</svg>'
(ASSETS / 'recent-activity.svg').write_text(svg, encoding='utf-8', newline='\n')
print('Refreshed public GitHub cards.')
