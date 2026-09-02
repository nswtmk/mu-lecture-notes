# -*- coding: utf-8 -*-
"""mU 2026 アーカイブサイト ビルダー

  data/subjects.json  →  index.html ＋ 各科目ページ

使い方:
    python3 build.py            # 生成
    python3 build.py --check    # Driveと照合して取りこぼしを警告（別途 check_drive.py）
"""
import json, os, sys, html

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(BASE, "data/subjects.json"), encoding="utf-8"))
SITE = DATA["site"]
STEPS = {s["no"]: s for s in DATA["steps"]}
SUBJECTS = DATA["subjects"]

E = html.escape
DRIVE = "https://drive.google.com/file/d/%s/view"

STATUS_LABEL = {"archived": "アーカイブ公開", "ongoing": "開講中", "upcoming": "開講前"}

# ============================================================ 共通CSS
CSS = """
  :root{
    --paper:#F6F5F1; --ink:#17171A; --sub:#5B5B63; --accent:#1130E8;
    --hairline:#DEDCD3; --black:#0D0D0F; --field:#0B7A45;
  }
  html{background:var(--paper);}
  body{
    margin:0;color:var(--ink);
    font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic Medium","Yu Gothic",-apple-system,sans-serif;
    font-size:16px;line-height:1.9;-webkit-font-smoothing:antialiased;
  }
  .hero{background:var(--black);color:#fff;padding:70px 24px 56px;}
  .hero-inner{max-width:940px;margin:0 auto;}
  .eyebrow{font-size:12px;letter-spacing:.34em;color:#9a9aa4;margin:0 0 24px;font-weight:600;}
  .hero h1{font-size:clamp(26px,4.6vw,38px);font-weight:700;letter-spacing:.02em;line-height:1.42;margin:0 0 12px;text-wrap:balance;}
  .hero .subtitle{font-size:15px;color:#c9c9d2;margin:0 0 32px;line-height:1.85;}
  .hstats{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:14px 26px;border-top:1px solid #2e2e34;padding-top:20px;font-size:13px;color:#c9c9d2;}
  .hstats b{color:#fff;font-size:18px;font-weight:700;margin-right:5px;}
  main{max-width:940px;margin:0 auto;padding:0 24px 96px;}
  h2{font-size:21px;font-weight:700;letter-spacing:.04em;margin:70px 0 8px;padding-top:22px;border-top:3px solid var(--ink);}
  h2 .h2-en{display:block;font-size:11px;letter-spacing:.3em;color:var(--accent);font-weight:600;margin-bottom:9px;}
  p{margin:14px 0;} .intro{font-size:16px;}
  a{color:var(--accent);text-underline-offset:3px;} strong{font-weight:700;}
  a.ai-btn{display:inline-block;background:var(--accent);color:#fff;font-size:12px;font-weight:700;letter-spacing:.03em;padding:7px 16px;border-radius:4px;text-decoration:none;}
  a.ai-btn:hover{background:#0B23B8;}
  .note{font-size:12.5px;color:var(--sub);background:#EFEEE8;border-radius:4px;padding:14px 18px;margin:26px 0 0;line-height:1.8;}
  .backlink{margin-top:70px;font-size:14px;}
  .access{border:1px solid #C5CEF7;background:#F0F3FE;border-radius:5px;padding:15px 19px;margin:22px 0 0;font-size:13.5px;line-height:1.85;}
  .access b{display:block;font-size:14.5px;margin-bottom:3px;}
  .forms-box{border:1px solid var(--hairline);background:#fff;border-radius:5px;padding:20px 24px 21px;margin:22px 0 0;}
  .forms-box b{display:block;font-size:15.5px;margin-bottom:3px;}
  .forms-box p{font-size:13.5px;color:var(--sub);line-height:1.85;margin:0 0 14px;}
  .forms-links{display:flex;flex-wrap:wrap;gap:9px;}
  /* --- 科目カード（トップ） --- */
  .cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;margin:18px 0 0;}
  a.card{display:block;background:#fff;border:1px solid var(--hairline);border-radius:6px;padding:18px 20px 17px;text-decoration:none;color:var(--ink);transition:transform .08s ease,border-color .12s ease;}
  a.card:hover{transform:translateY(-2px);border-color:var(--accent);}
  a.card.upcoming{background:#FAFAF7;}
  .card-top{display:flex;align-items:center;gap:9px;margin-bottom:7px;}
  .card-ic{font-size:19px;line-height:1;}
  .card-badge{margin-left:auto;font-size:10.5px;font-weight:700;letter-spacing:.06em;padding:3px 9px;border-radius:999px;white-space:nowrap;}
  .b-archived{background:var(--accent);color:#fff;}
  .b-ongoing{background:var(--field);color:#fff;}
  .b-upcoming{background:#EFEEE8;color:var(--sub);}
  .card-name{font-size:16.5px;font-weight:700;letter-spacing:.02em;line-height:1.45;}
  .card-meta{font-size:12px;color:var(--sub);line-height:1.7;margin-top:5px;}
  .card-count{font-size:11.5px;color:var(--accent);font-weight:700;margin-top:7px;letter-spacing:.03em;}
  .step-head{display:flex;align-items:baseline;gap:14px;border-top:3px solid var(--ink);padding-top:18px;margin:56px 0 4px;}
  .step-no{font-size:11px;letter-spacing:.26em;color:var(--accent);font-weight:700;white-space:nowrap;}
  .step-head h2{font-size:19px;margin:0;border:none;padding:0;}
  .step-msg{font-size:12.5px;color:var(--sub);margin:0 0 6px;}
  .field-sec{margin-top:64px;border-top:3px solid var(--field);padding-top:20px;}
  .field-sec h2{border:none;padding:0;margin:0 0 4px;color:var(--field);}
  .field-sec .step-msg{margin-bottom:8px;}
  a.card.field:hover{border-color:var(--field);}
  .program-note{font-size:13px;background:#fff;border:1px solid var(--hairline);border-radius:6px;padding:16px 20px;margin:24px 0 0;line-height:1.9;}
  /* --- 各回ブロック（科目ページ） --- */
  .lec{border:1px solid var(--hairline);background:#fff;border-radius:5px;padding:22px 24px 20px;margin:16px 0;}
  .lec-head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:4px;}
  .lec-no{font-size:13px;font-weight:700;color:var(--accent);font-variant-numeric:tabular-nums;letter-spacing:.08em;}
  .lec-date{font-size:12.5px;color:var(--sub);font-variant-numeric:tabular-nums;}
  .lec-title{font-size:17.5px;font-weight:700;line-height:1.55;margin:2px 0 3px;}
  .lec-lecturer{font-size:13px;color:var(--sub);margin:0 0 12px;}
  .lec-gist{font-size:14.5px;line-height:1.9;margin:0 0 14px;}
  .kw{display:flex;flex-wrap:wrap;gap:7px;margin:0 0 15px;}
  .kw span{font-size:11.5px;color:var(--accent);border:1px solid #C5CEF7;background:#F0F3FE;border-radius:3px;padding:3px 9px;letter-spacing:.02em;}
  .lec-links{display:flex;flex-wrap:wrap;gap:9px;align-items:center;}
  .open-card{display:flex;align-items:center;gap:16px;text-decoration:none;border-radius:5px;padding:16px 20px;margin:6px 0 10px;transition:transform .08s ease;}
  .open-card:hover{transform:translateY(-1px);}
  .open-card .ic{flex-shrink:0;width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:17px;line-height:1;}
  .open-card .tx{min-width:0;}
  .open-card .t1{display:block;font-size:15px;font-weight:700;line-height:1.5;}
  .open-card .t2{display:block;font-size:12.5px;line-height:1.6;margin-top:1px;}
  .open-card .arrow{margin-left:auto;flex-shrink:0;font-size:15px;font-weight:700;}
  .card-video{background:var(--black);border:1px solid var(--black);}
  .card-video .ic{background:#fff;color:var(--black);}
  .card-video .t1{color:#fff;} .card-video .t2{color:#b6b6c0;} .card-video .arrow{color:#fff;}
  .card-slide{background:#fff;border:1px solid var(--hairline);}
  .card-slide .ic{background:#F0F3FE;color:var(--accent);border:1px solid #C5CEF7;}
  .card-slide .t1{color:var(--ink);} .card-slide .t2{color:var(--sub);} .card-slide .arrow{color:var(--accent);}
  .card-slide:hover{border-color:var(--accent);}
  .lines{margin:20px 0;padding:0;list-style:none;counter-reset:ln;}
  .lines li{counter-increment:ln;position:relative;padding:0 0 0 44px;margin:20px 0;}
  .lines li::before{content:counter(ln,decimal-leading-zero);position:absolute;left:0;top:3px;font-size:12.5px;font-weight:700;color:var(--accent);font-variant-numeric:tabular-nums;letter-spacing:.05em;}
  .lines b{display:block;font-size:15.5px;margin-bottom:1px;}
  .lines span{font-size:14px;color:var(--sub);line-height:1.85;display:block;}
  .kadai{border:1px solid var(--accent);border-radius:5px;background:#fff;padding:22px 24px 21px;margin:18px 0;}
  .kadai .k-label{display:inline-block;background:var(--accent);color:#fff;font-size:10.5px;font-weight:700;letter-spacing:.16em;padding:3px 9px;border-radius:3px;margin-bottom:9px;}
  .kadai .k-title{font-size:17px;font-weight:700;display:block;margin-bottom:4px;}
  .kadai .k-desc{font-size:13.5px;color:var(--sub);line-height:1.85;margin:0 0 14px;}
  .kadai .k-links{display:flex;flex-wrap:wrap;gap:9px;}
  .prep{border:1px dashed #CFCEC6;background:#FAFAF7;border-radius:5px;padding:24px 26px;margin:22px 0;}
  .prep b{display:block;font-size:16px;margin-bottom:6px;}
  .prep p{font-size:14px;color:var(--sub);margin:0 0 10px;line-height:1.9;}
  .info-tbl{width:100%;border-collapse:collapse;margin:18px 0;font-size:14px;}
  .info-tbl th{text-align:left;width:120px;padding:10px 10px 10px 0;border-bottom:1px solid var(--hairline);color:var(--sub);font-weight:600;font-size:12.5px;vertical-align:top;white-space:nowrap;}
  .info-tbl td{padding:10px 0;border-bottom:1px solid var(--hairline);}
"""

HEAD = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex">
<title>%(title)s</title>
<style>%(css)s</style>
</head>
<body>
"""

FOOT = "\n</main>\n</body>\n</html>\n"


def access_block():
    return ('<div class="access"><b>視聴にはアクセス権が必要です</b>'
            '受講生限定の配信です。動画・スライドのカードをクリックすると、Googleドライブが別ウィンドウで開きます。'
            '「アクセス権が必要です」と表示される場合は、受講にお使いのGoogleアカウントでログインしているかご確認ください。'
            'ログイン済みでも開けない場合は、mU事務局（%s）までお問い合わせください。</div>' % SITE["contact"])


def forms_block():
    return ('<div class="forms-box">\n'
            '  <b>感想と質問をお寄せください</b>\n'
            '  <p><strong>各回の感想のご提出は出席認定に必要です。</strong>'
            'アーカイブ視聴後にお忘れなくご提出ください。講義内容への質問は質問フォームへどうぞ。</p>\n'
            '  <div class="forms-links">\n'
            '    <a class="ai-btn" href="%s" target="_blank" rel="noopener">感想フォーム</a>\n'
            '    <a class="ai-btn" href="%s" target="_blank" rel="noopener">質問フォーム</a>\n'
            '  </div>\n</div>\n' % (SITE["forms"]["kansou"], SITE["forms"]["shitsumon"]))


def open_card(kind, url, t1, t2):
    ic = "▶" if kind == "video" else "▤"
    cls = "card-video" if kind == "video" else "card-slide"
    return ('<a class="open-card %s" href="%s" target="_blank" rel="noopener">\n'
            '    <span class="ic">%s</span>\n'
            '    <span class="tx"><span class="t1">%s</span><span class="t2">%s</span></span>\n'
            '    <span class="arrow">↗</span>\n  </a>\n' % (cls, url, ic, E(t1), E(t2)))


NOTE_OPEN = "クリックすると別ウィンドウで開きます（Googleアカウントのログインが必要）"


def lecture_block(s, L):
    o = ['<div class="lec">']
    o.append('  <div class="lec-head"><span class="lec-no">%02d</span><span class="lec-date">%s</span></div>'
             % (L["no"], E(L["date"])))
    o.append('  <p class="lec-title">%s</p>' % E(L["title"]))
    o.append('  <p class="lec-lecturer">%s</p>' % E(L["lecturer"]))
    unit = "講" if s["slug"].startswith("aishakai") else "回"
    if L.get("video"):
        o.append('  ' + open_card("video", DRIVE % L["video"],
                                  "第%d%s 講義アーカイブ動画を見る" % (L["no"], unit), NOTE_OPEN))
    for sl in L.get("slides", []):
        o.append('  ' + open_card("slide", DRIVE % sl["id"], sl["label"], NOTE_OPEN))
    if L.get("gist"):
        o.append('  <p class="lec-gist">%s</p>' % L["gist"])
    if L.get("keywords"):
        o.append('  <div class="kw">%s</div>' % "".join("<span>%s</span>" % E(k) for k in L["keywords"]))
    if L.get("summary") or L.get("voices"):
        links=[]
        if L.get("summary"):
            links.append('<a class="ai-btn" href="%s">AIまとめを読む</a>' % L["summary"])
        if L.get("voices"):
            links.append('<a class="ai-btn" href="%s">受講生の感想を読む</a>' % L["voices"])
        o.append('  <div class="lec-links">%s</div>' % "".join(links))
    o.append('</div>\n')
    return "\n".join(o)


def subject_page(s):
    step = STEPS[s["step"]]
    kind = "フィールド講義" if s["mode"] == "field" else "オンライン講義"
    title = "%s｜%s" % (s["name"], "アーカイブ視聴 & AIまとめ" if s["lectures"] else kind)
    o = [HEAD % {"title": E(title), "css": CSS}]
    o.append('<header class="hero">\n  <div class="hero-inner">')
    o.append('    <p class="eyebrow">MAKERS UNLEARN 2026 ｜ STEP %d %s ｜ %s</p>' % (step["no"], E(step["title"]), kind))
    o.append('    <h1>%s</h1>' % E(s["name"]))
    o.append('    <p class="subtitle">%s</p>' % E(s["desc"]))
    stats = [(s["count"], ""), (s["period"], ""), (STATUS_LABEL[s["status"]], "")]
    o.append('    <div class="hstats">')
    o.append('      <div><b>%s</b></div>' % E(s["count"]))
    o.append('      <div><b>%s</b></div>' % E(s["period"]))
    if s.get("place"):
        o.append('      <div><b>%s</b></div>' % E(s["place"]))
    o.append('      <div><b>%s</b></div>' % STATUS_LABEL[s["status"]])
    o.append('    </div>\n  </div>\n</header>\n\n<main>\n')

    if s["lectures"]:
        o.append('<p class="intro">全%d%sの講義アーカイブ動画・講義スライド・まとめレポート（AIまとめ）をまとめた視聴ページです。'
                 '動画とスライドはカードをクリックすると別ウィンドウで開きます。</p>'
                 % (len(s["lectures"]), "講" if s["slug"].startswith("aishakai") else "回"))
        o.append(access_block())
        o.append(forms_block())
        if s.get("extraSummary"):
            o.append('<div class="kadai"><span class="k-label">まとめ</span>'
                     '<span class="k-title">%s</span>'
                     '<div class="k-links"><a class="ai-btn" href="%s">まとめを読む</a></div></div>'
                     % (E(s["extraSummary"]["label"]), s["extraSummary"]["url"]))
        o.append('\n<h2><span class="h2-en">LECTURES</span>アーカイブ</h2>\n')
        for L in s["lectures"]:
            o.append(lecture_block(s, L))
        if s.get("throughlines"):
            o.append('\n<h2><span class="h2-en">THROUGHLINES</span>この科目を貫いた線</h2>')
            o.append('<ol class="lines">')
            for t in s["throughlines"]:
                o.append('  <li><b>%s</b><span>%s</span></li>' % (E(t["b"]), E(t["s"])))
            o.append('</ol>\n')
        if s.get("assignment"):
            a = s["assignment"]
            o.append('\n<h2><span class="h2-en">ASSIGNMENT</span>最終課題</h2>')
            o.append('<div class="kadai">\n  <span class="k-label">最終課題</span>')
            o.append('  <span class="k-title">%s</span>' % E(a["title"]))
            o.append('  <p class="k-desc">%s</p>' % E(a["desc"]))
            links = ['<a class="ai-btn" href="%s">最終課題を見る</a>' % a["page"]]
            if a.get("material"):
                links.append('<a class="ai-btn" href="%s">%s</a>' % (a["material"]["url"], E(a["material"]["label"])))
            if a.get("form"):
                links.append('<a class="ai-btn" href="%s" target="_blank" rel="noopener">最終課題を提出する</a>' % a["form"])
            o.append('  <div class="k-links">%s</div>\n</div>\n' % "".join(links))
        o.append('<div class="note">各レポートは講義アーカイブ動画の自動文字起こしとスクリーンショットから生成したまとめです。'
                 '発言の要旨は文字起こしに基づき編集していますが、細部のニュアンスは実際の講義動画をご確認ください。'
                 '受講生の氏名・発言は匿名化しています。</div>')
    else:
        # 開講前
        o.append('<p class="intro">%s</p>' % E(s["desc"]))
        o.append('<table class="info-tbl">')
        o.append('<tr><th>形式</th><td>%s</td></tr>' % kind)
        o.append('<tr><th>日程</th><td>%s</td></tr>' % E(s["schedule"]))
        if s.get("place"):
            o.append('<tr><th>会場</th><td>%s</td></tr>' % E(s["place"]))
        o.append('<tr><th>ボリューム</th><td>%s</td></tr>' % E(s["count"]))
        o.append('<tr><th>講師</th><td>%s</td></tr>' % E(s["lecturers"]))
        o.append('</table>')
        if s["mode"] == "field":
            o.append('<div class="prep"><b>開催に向けたご案内</b>'
                     '<p>集合場所・アクセス・持ち物・当日の流れは、開催が近づきましたらこのページと受講生向けのご案内でお知らせします。</p>'
                     '<p>開催後は、当日の記録（写真・動画）とレポートをこのページに掲載します。</p></div>')
        else:
            o.append('<div class="prep"><b>この科目はこれから開講します</b>'
                     '<p>講義アーカイブ動画・講義スライド・AIまとめレポートは、開講後に各回ぶんを順次このページへ追加していきます。</p>'
                     '<p>受講にはアクセス権（Googleアカウント）が必要です。開講前にご案内します。</p></div>')
        o.append(forms_block())
        if s.get("peatix"):
            o.append('<p style="margin-top:22px;"><a class="ai-btn" href="%s" target="_blank" rel="noopener">申込（Peatix）</a></p>' % s["peatix"])

    o.append('<p class="backlink"><a href="index.html">← 全科目一覧に戻る</a></p>')
    o.append(FOOT)
    return "\n".join(o)


def card(s):
    cls = "card"
    if s["status"] == "upcoming":
        cls += " upcoming"
    if s["mode"] == "field":
        cls += " field"
    o = ['<a class="%s" href="%s.html">' % (cls, s["slug"])]
    o.append('  <div class="card-top"><span class="card-ic">%s</span>'
             '<span class="card-badge b-%s">%s</span></div>' % (s["icon"], s["status"], STATUS_LABEL[s["status"]]))
    o.append('  <div class="card-name">%s</div>' % E(s["name"]))
    o.append('  <div class="card-meta">%s<br>%s</div>' % (E(s["lecturers"][:44] + ("…" if len(s["lecturers"]) > 44 else "")), E(s["schedule"])))
    o.append('  <div class="card-count">%s</div>' % E(s["count"]))
    o.append('</a>')
    return "\n".join(o)


def index_page():
    online = [s for s in SUBJECTS if s["mode"] == "online"]
    field = [s for s in SUBJECTS if s["mode"] == "field"]
    archived = sum(1 for s in SUBJECTS if s["status"] == "archived")
    o = [HEAD % {"title": "makers Unlearn 2026｜科目アーカイブ", "css": CSS}]
    o.append('<header class="hero">\n  <div class="hero-inner">')
    o.append('    <p class="eyebrow">MAKERS UNLEARN 2026</p>')
    o.append('    <h1>科目アーカイブ</h1>')
    o.append('    <p class="subtitle">%s　哲学・人類学・デザイン・エンジニアリング・社会実装を横断して学ぶプログラム</p>' % E(SITE["tagline"]))
    o.append('    <div class="hstats">')
    o.append('      <div><b>12</b>科目 210時間</div>')
    o.append('      <div><b>50+</b>名の専門家・実務家</div>')
    o.append('      <div><b>2026.7</b>—2027.3 開講</div>')
    o.append('      <div><b>%d</b>科目 アーカイブ公開中</div>' % archived)
    o.append('    </div>\n  </div>\n</header>\n\n<main>\n')
    o.append('<p class="intro">makers Unlearn 2026 の全科目アーカイブです。'
             '科目をクリックすると、講義動画・講義スライド・AIまとめレポート・感想フォーム・課題が'
             'まとまった科目ページが開きます。</p>')
    o.append('<div class="program-note"><b>受講のしくみ</b>：全12科目（オンライン講義8科目＋フィールド講義4科目）から自由に'
             '<b>5科目を選択</b>して受講し、各科目の課題提出を完了すると<b>修了認定証</b>が発行されます'
             '（Techキャンプは2科目分、AIと社会はⅠ〜Ⅲ合わせて1科目分）。オンライン講義はアーカイブ配信あり'
             '（<b>%s まで視聴可</b>）。詳細は<a href="%s">公式サイト</a>・申込は<a href="%s">Peatix</a>へ。</div>'
             % (SITE["viewUntil"], SITE["official"], SITE["peatix"]))
    for n in (1, 2, 3, 4):
        subs = [s for s in online if s["step"] == n]
        if not subs:
            continue
        st = STEPS[n]
        o.append('\n<div class="step-head"><span class="step-no">STEP %d</span><h2>%s</h2></div>' % (n, E(st["title"])))
        o.append('<p class="step-msg">%s</p>' % E(st["msg"]))
        o.append('<div class="cards">')
        for s in subs:
            o.append(card(s))
        o.append('</div>')
    o.append('\n<div class="field-sec">')
    o.append('<h2>フィールド講義</h2>')
    o.append('<p class="step-msg">現地に集まって身体で学ぶ講義。開催後は当日の記録とレポートを掲載します。</p>')
    o.append('<div class="cards">')
    for s in field:
        o.append(card(s))
    o.append('</div>\n</div>')
    o.append('<div class="note">このサイトは受講生・講師向けの限定アーカイブです。'
             '動画・スライドの視聴には、受講にお使いのGoogleアカウントでのログインが必要です。'
             'ご不明な点は mU事務局（%s）まで。</div>' % SITE["contact"])
    o.append(FOOT)
    return "\n".join(o)


def main():
    written = []
    open(os.path.join(BASE, "index.html"), "w", encoding="utf-8").write(index_page())
    written.append("index.html")
    for s in SUBJECTS:
        p = "%s.html" % s["slug"]
        open(os.path.join(BASE, p), "w", encoding="utf-8").write(subject_page(s))
        written.append(p)
    print("生成:", len(written), "ページ")
    for w in written:
        print("  -", w)


if __name__ == "__main__":
    main()
