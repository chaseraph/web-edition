"""Build the News in the Grove Web Edition from Ghost API data."""
import json
import re

with open('web-edition/ghost-stories.json', 'r', encoding='utf-8') as f:
    posts = json.load(f)

# Filter: since Feb 13, no newsletters
stories = []
for p in posts:
    tags = [t['name'] for t in p.get('tags', []) if not t['name'].startswith('#')]
    if 'Newsletter' in tags:
        continue
    if p['published_at'] < '2026-02-13':
        continue
    stories.append({
        'title': p['title'],
        'slug': p['slug'],
        'html': p.get('html', ''),
        'excerpt': p.get('custom_excerpt', ''),
        'image': p.get('feature_image', ''),
        'image_caption': p.get('feature_image_caption', ''),
        'author': p.get('authors', [{}])[0].get('name', 'Unknown'),
        'date': p['published_at'][:10],
        'tags': tags,
        'reading_time': p.get('reading_time', 0),
    })

# Sort: local stories first, state politics last
def story_priority(s):
    tag_order = {
        'Weather': 1,
        'Forest Grove': 2,
        'Community': 3,
        'Education': 4,
        'Crime': 5,
        'Recreation': 6,
        'History': 7,
        'Government': 8,
        'Politics': 9,
    }
    for tag in s['tags']:
        if tag in tag_order:
            return tag_order[tag]
    return 5

stories.sort(key=story_priority)

def clean_html(html):
    html = re.sub(r'<!--kg-card-begin: html-->', '', html)
    html = re.sub(r'<!--kg-card-end: html-->', '', html)
    html = re.sub(r'<div style="font-family:[^"]*"[^>]*>', '<div>', html)
    return html.strip()

def format_date(d):
    months = {'01':'January','02':'February','03':'March','04':'April','05':'May','06':'June',
              '07':'July','08':'August','09':'September','10':'October','11':'November','12':'December'}
    parts = d.split('-')
    return f"{months[parts[1]]} {int(parts[2])}, {parts[0]}"

def tag_label(tags):
    priority = ['Weather','Forest Grove','Education','Crime','Recreation','History','Community','Government','Politics']
    for p in priority:
        if p in tags:
            return p
    return tags[0] if tags else ''

def extract_pull_quote(html):
    paragraphs = re.findall(r'<p>(.*?)</p>', html, re.DOTALL)
    if len(paragraphs) < 5:
        return None
    start = len(paragraphs) // 3
    end = 2 * len(paragraphs) // 3
    for p in paragraphs[start:end]:
        text = re.sub(r'<[^>]+>', '', p)
        match = re.search(r'\u201c([^\u201d]+)\u201d', text)
        if match and 40 < len(match.group(1)) < 250:
            return match.group(1)
        match = re.search(r'"([^"]+)"', text)
        if match and 40 < len(match.group(1)) < 250:
            return match.group(1)
    return None

def should_have_dropcap(html):
    match = re.search(r'<p>(.*?)</p>', html, re.DOTALL)
    if not match:
        return False
    first_p = match.group(1).strip()
    if first_p.startswith('<em>') or first_p.startswith('<strong>') or first_p.startswith('<a'):
        return False
    plain = re.sub(r'<[^>]+>', '', first_p)
    if len(plain) < 50:
        return False
    if plain and not plain[0].isalpha():
        return False
    return True

def insert_pull_quote(html, quote):
    pq_html = f'\n<blockquote class="pull-quote">\u201c{quote}\u201d</blockquote>\n'
    pos = 0
    for i in range(4):
        pos = html.find('</p>', pos)
        if pos == -1:
            return html
        pos += 4
    return html[:pos] + pq_html + html[pos:]

def is_history_stub(s):
    return 'History' in s['tags']

def history_stub_block(s):
    """Render a history column as a compact stub with feature image + read more."""
    tag = tag_label(s['tags'])

    deck_html = ''
    if s.get('excerpt'):
        deck_html = f'<p class="deck">{s["excerpt"]}</p>'

    img_html = ''
    if s['image']:
        img_html = f'<img src="{s["image"]}" alt="{s["title"]}" loading="lazy">'

    post_url = f'https://www.newsinthegrove.com/{s["slug"]}/'

    return f'''<article class="story story-stub" id="{s['slug']}">
      <div class="stub-layout">
        <div class="stub-image">
          {img_html}
        </div>
        <div class="stub-text">
          <span class="tag">{tag}</span>
          <h2>{s['title']}</h2>
          {deck_html}
          <p class="meta">
            <span class="author">By {s['author']}</span>
            <span class="date">&bull; {format_date(s['date'])}</span>
          </p>
          <p class="stub-cta"><a href="{post_url}">Read the full column &rarr;</a></p>
        </div>
      </div>
    </article>'''

def story_block(s, is_lead=False):
    if is_history_stub(s):
        return history_stub_block(s)

    tag = tag_label(s['tags'])

    body = clean_html(s['html'])

    # Only show hero image if it's NOT already in the body HTML
    img_html = ''
    if s['image'] and s['image'] not in body:
        cap = f'<figcaption>{s["image_caption"]}</figcaption>' if s.get('image_caption') else ''
        img_html = f'''<figure class="story-hero-img">
          <img src="{s['image']}" alt="{s['title']}" loading="lazy">
          {cap}
        </figure>'''

    quote = extract_pull_quote(body)
    if quote:
        body = insert_pull_quote(body, quote)

    dropcap_cls = ' has-dropcap' if should_have_dropcap(body) else ''

    deck_html = ''
    if s.get('excerpt'):
        deck_html = f'<p class="deck">{s["excerpt"]}</p>'

    cls = 'story lead-story' if is_lead else 'story'

    return f'''<article class="{cls}" id="{s['slug']}">
      <div class="story-header">
        <span class="tag">{tag}</span>
        <h2>{s['title']}</h2>
        {deck_html}
        <p class="meta">
          <span class="author">By {s['author']}</span>
          <span class="date">&bull; {format_date(s['date'])}</span>
          <span class="reading-time">&bull; {s['reading_time']} min read</span>
        </p>
      </div>
      {img_html}
      <div class="story-body{dropcap_cls}">
        {body}
      </div>
    </article>'''

# Layout: lead + two sections
lead = stories[0]
rest = stories[1:]
mid_break = len(rest) // 2
first_half = rest[:mid_break]
second_half = rest[mid_break:]

# Story index
index_items = ''
for s in stories:
    index_items += f'        <li><a href="#{s["slug"]}">{s["title"]}</a></li>\n'

# Events data
events = {
    'Tuesday, February 17': [
        ('10:00 am', 'Preschool Storytime', 'Forest Grove City Library', 'preschool-storytime/17759265/2026-02-17T10'),
        ('2:00 pm', 'Pacific U JV Baseball vs Clark College', 'Chuck Bafaro Stadium', 'pacific-university-athletics-jv-baseball-vs-clark-college/18132578/2026-02-17T14'),
        ('4:00 pm', 'Chess Club', 'Forest Grove City Library', 'chess-club/17759266/2026-02-17T16'),
        ('5:30 pm', 'Pacific U Women\u2019s Basketball vs George Fox', 'Stoller Center', 'pacific-university-athletics-women-s-basketball-vs-george-fox-university/18132579/2026-02-17T17'),
        ('6:00 pm', 'Advanced Line Dance Practice', 'Zesti Food Carts', 'adv-line-dance-practice/17847729/2026-02-17T18'),
        ('7:00 pm', 'Tuesday Trivia at Waltz', 'Waltz Brewing', 'tuesday-trivia-at-waltz/16180242/2026-02-17T19'),
        ('7:30 pm', 'Pacific U Men\u2019s Basketball vs George Fox', 'Stoller Center', 'pacific-university-athletics-men-s-basketball-vs-george-fox-university/18132580/2026-02-17T19'),
    ],
    'Wednesday, February 18': [
        ('10:00 am', 'Historic Forest Grove Museum & Library', 'Old Train Station', 'friends-of-historic-forest-grove-museum-library-open/16072367/2026-02-18T10'),
        ('10:55 am', 'Gales Creek Gleaners', 'Gales Creek Community Church', 'gales-creek-gleaners/16083114/2026-02-18T10'),
        ('11:00 am', 'AARP Foundation Tax-Aide', 'Forest Grove City Library', 'aarp-foundation-tax-aide/18041486/2026-02-18T11'),
        ('4:00 pm', 'Teen Zone Crafting Hour', 'Forest Grove City Library', 'teen-zone-crafting-hour/17759267/2026-02-18T16'),
        ('5:00 pm', 'Indoor Climbing \u2014 Outdoor Pursuits', 'The Creamery', 'indoor-climbing-outdoor-pursuits/18117047/2026-02-18T17'),
        ('6:30 pm', 'Cub Scouts Pack 169', 'Holbrook Masonic Lodge', 'cub-scouts-pack-169/17998186/2026-02-18T18'),
        ('7:00 pm', 'Pods & Pints \u2014 Podcast Club', 'Waltz Brewing', 'pods-pints-podcast-club-at-waltz/17651241/2026-02-18T19'),
    ],
    'Thursday, February 19': [
        ('5:00 pm', 'Public Arts Commission', 'Forest Grove', 'public-arts-commission/18041487/2026-02-19T17'),
        ('6:00 pm', 'Gales Creek Library', 'Gales Creek Elementary School', 'gales-creek-library/17155099/2026-02-19T18'),
        ('6:00 pm', 'Bluegrass Jam Session', 'Waltz Brewing', 'bluegrass-jam-session/16180245/2026-02-19T18'),
        ('7:00 pm', 'Open Mic Night', 'Taqueria Corona', 'open-mic/17847956/2026-02-19T19'),
        ('7:30 pm', 'Mojo Holler', 'McMenamins Grand Lodge', 'mojo-holler-at-mcmenamins-grand-lodge/17995868/2026-02-19T19'),
    ],
    'Friday, February 20': [
        ('10:00 am', 'Digital Navigator: Tech Assistance', 'Forest Grove City Library', 'digital-navigator-one-on-one-tech-assistance/17088270/2026-02-20T10'),
        ('10:15 am', 'Senior Stretch', 'Forest Grove', 'senior-stretch/18041492/2026-02-20T10'),
    ],
}

events_html = ''
for day, evts in events.items():
    items = ''
    for time, title, venue, slug in evts:
        url = f'https://www.newsinthegrove.com/events/#/details/{slug}'
        items += f'''<a class="event-card" href="{url}">
              <span class="event-time">{time}</span>
              <div class="event-details">
                <strong>{title}</strong>
                <span class="event-venue">{venue}</span>
              </div>
            </a>\n'''
    events_html += f'''<div class="events-day-group">
          <h3 class="events-day-label">{day}</h3>
          <div class="events-list">{items}</div>
        </div>\n'''

# Build story sections
first_half_html = ''
for i, s in enumerate(first_half):
    first_half_html += story_block(s)
    if i < len(first_half) - 1:
        first_half_html += '\n      <hr class="story-rule">\n'

second_half_html = ''
for i, s in enumerate(second_half):
    second_half_html += story_block(s)
    if i < len(second_half) - 1:
        second_half_html += '\n      <hr class="story-rule">\n'

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>News in the Grove &mdash; Web Edition | February 17, 2026</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,400;0,6..72,600;0,6..72,700;1,6..72,400;1,6..72,600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
</head>
<body>

  <div class="top-bar">
    <div class="container-wide">
      <span>Forest Grove &bull; Gales Creek &bull; Western Washington County</span>
      <span><a href="https://www.newsinthegrove.com/signup/">Subscribe</a> &bull; <a href="https://www.newsinthegrove.com/events/">Events</a> &bull; <a href="https://tips.newsinthegrove.com/">Submit a Tip</a></span>
    </div>
  </div>

  <header class="masthead">
    <div class="container">
      <h1 class="masthead-title"><a href="https://www.newsinthegrove.com">News <em>in the</em> Grove</a></h1>
      <p class="masthead-subtitle">Community-driven digital newspaper</p>
      <p class="masthead-date">Tuesday, February 17, 2026</p>
    </div>
  </header>

  <div class="alert-banner">
    <div class="container-wide">
      Winter weather advisory in effect for Coast Range foothills through Friday &mdash; valley snow possible Wednesday evening
    </div>
  </div>

  <nav class="story-index">
    <div class="container">
      <h2 class="story-index-title">In This Edition</h2>
      <ul class="story-index-list">
{index_items}      </ul>
    </div>
  </nav>

  <main>

    <div class="container">
      {story_block(lead, is_lead=True)}
    </div>

    <div class="container">
      <div class="section-divider"><span>More News</span></div>
      {first_half_html}
    </div>

    <section class="events-section">
      <div class="container-wide">
        <h2 class="section-header">Community Calendar</h2>
        <p class="events-sponsor">Sponsored by Uncommon Grove, Welcome Home Realty, Waltz Brewing &amp; the City of Banks</p>
        {events_html}
        <p class="events-cta"><a href="https://www.newsinthegrove.com/events/">View all events &amp; submit yours at newsinthegrove.com/events &rarr;</a></p>
      </div>
    </section>

    <div class="container">
      <div class="section-divider"><span>Features &amp; Columns</span></div>
      {second_half_html}
    </div>

    <div class="container">
      <div class="subscribe-cta">
        <h3>Get the Friday newsletter</h3>
        <p>Every Friday, we send links to stories, exclusive newsletter-only content, and 35+ community events. Free to subscribe.</p>
        <a href="https://www.newsinthegrove.com/#/portal/signup" class="btn">Subscribe free</a>
      </div>
    </div>

  </main>

  <footer class="footer">
    <div class="container-wide">
      <div class="footer-inner">
        <span class="footer-brand">News <em>in the</em> Grove</span>
        <nav class="footer-links">
          <a href="https://www.newsinthegrove.com">Home</a>
          <a href="https://www.newsinthegrove.com/events/">Events</a>
          <a href="https://www.newsinthegrove.com/about/">About</a>
          <a href="https://www.newsinthegrove.com/contact/">Contact</a>
          <a href="https://www.newsinthegrove.com/advertise/">Advertise</a>
          <a href="https://www.facebook.com/forestgrovenews">Facebook</a>
        </nav>
        <p class="footer-copy">&copy; 2026 News in the Grove LLC &bull; Published by Firestarter Media</p>
      </div>
    </div>
  </footer>

</body>
</html>'''

with open('web-edition/index.html', 'w', encoding='utf-8') as f:
    f.write(page)

print('Built web-edition/index.html')
print(f'  Story order:')
for i, s in enumerate(stories):
    marker = '>> LEAD' if i == 0 else f'   #{i+1}'
    print(f'    {marker}: [{tag_label(s["tags"])}] {s["title"][:60]}')
print(f'  Pull quotes: {sum(1 for s in stories if extract_pull_quote(clean_html(s["html"])))}')
print(f'  Drop caps: {sum(1 for s in stories if should_have_dropcap(clean_html(s["html"])))}')
