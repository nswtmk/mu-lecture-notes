/**
 * mU配信素材 権限監査スクリプト（2026-08-23）
 *
 * 目的
 *   1) 科目ごとの受講生が、その科目の動画・スライドを見られる状態か
 *   2) 受講していない科目が見えてしまっていないか
 *   を Drive の実ACLで確認する。
 *
 * 使い方
 *   1. https://script.google.com/home/projects/create を開く
 *   2. この中身を全部貼り付けて保存
 *   3. 左メニュー「サービス」＋ → Drive API → 追加（識別子は Drive のまま）
 *   4. auditAll を選んで「実行」→ 初回だけ承認ダイアログで許可
 *   5. 「実行ログ」を見る。結果はスプレッドシートにも書き出される
 *
 * 名簿の出典: mU2026 アカウント管理シート gid=755094016 ほか科目別タブ
 *   法人プラン（concentinc.jp / keipe.co.jp / pref.yamanashi.lg.jp / rmd.co.jp /
 *   nxera.life / loftwork.com / phive.tokyo / tycoonrunning.com / condenast.jp）は
 *   今回の対象外なので「法人」として別枠に集計し、過剰付与には数えない。
 */

var CORP_DOMAINS = ["concentinc.jp", "keipe.co.jp", "keipe-connect.co.jp", "pref.yamanashi.lg.jp", "rmd.co.jp", "nxera.life", "loftwork.com", "phive.tokyo", "tycoonrunning.com", "condenast.jp"];

var SUBJECTS = {
  "テクノロジーの未来学": {
    "roster": [
      "27kasairio@shibushibu.ed.jp",
      "air285962aw@gmail.com",
      "anythingone123@gmail.com",
      "ayako.katano.0614@gmail.com",
      "bonnou108@mac.com",
      "dantanyh49@gmail.com",
      "ehlytjp@gmail.com",
      "f.tomohisa26@gmail.com",
      "g2460117@edu.cc.ocha.ac.jp",
      "gymratsjk@gmail.com",
      "handa.tsukuba@gmail.com",
      "hhirakawa001@gmail.com",
      "hideaki_owa@hotmail.com",
      "hideakiowa@gmail.com",
      "hiro@hsgw.co",
      "honamifurugaki@gmail.com",
      "i-tomoya@mars.dti.ne.jp",
      "i.franem22@gmail.com",
      "i.sengoku@code.or.jp",
      "info@haloclineweb.com",
      "info@issueplusdesign.jp",
      "ishibaa.55@gmail.com",
      "ishiishify@gmail.com",
      "itomo2007@gmail.com",
      "jun0307kamosida@gmail.com",
      "kaishyu.110211@gmail.com",
      "kazu.mura@ezweb.ne.jp",
      "kenuesaka@icloud.com",
      "kimiwatanabe3@gmail.com",
      "kobayuji.0909@gmail.com",
      "komorebi496@gmail.com",
      "kosukeinoue.ki@gmail.com",
      "kozo555@gmail.com",
      "kumataro0608jp@yahoo.co.jp",
      "liu.yi@outlook.jp",
      "longvalleyriver.k516@gmail.com",
      "longvalleyriver.k516@icloud.com",
      "mayamamoto5@gmail.com",
      "mayuaoki.nw@gmail.com",
      "meg.furush@gmail.com",
      "miyazakitatsuro@gmail.com",
      "mizukami@hototo.jp",
      "npjs0407@gmail.com",
      "okada@ande.ink",
      "pinksaloonrock@gmail.com",
      "putomo@aol.com",
      "s.k.tableaux@gmail.com",
      "sachi.shiraki@gmail.com",
      "sanbonmatsu@icr.co.jp",
      "saori.nakai.my@gmail.com",
      "sasaki.s@dentsudigital.co.jp",
      "shina47rika@gmail.com",
      "shirota.ichiro@gmail.com",
      "sn7131923@gmail.com",
      "suzukimasanori@gmail.com",
      "takada@neptune.kanazawa-it.ac.jp",
      "tatsuro_handa@me.com",
      "tdaikoku.tky@gmail.com",
      "tm.ishizu@gmail.com",
      "tomourabe97@gmail.com",
      "tsuburakobayashi@gmail.com",
      "tsugu28@gmail.com",
      "tsumura-kei@asakonet.co.jp",
      "une.dance04.oto02@gmail.com",
      "utakata.philosopher@gmail.com",
      "xiangmiao12@gmail.com",
      "ykyosuke0224@gmail.com",
      "yuki.osh@gmail.com",
      "yuuki.hirabayashi+2@gmail.com",
      "yuuki.hirabayashi@gmail.com",
      "zhangqiang960517@gmail.com",
      "zhangqiang960517@outlook.com",
      "zhibaolidao2@gmail.com",
      "zhouaijia8@gmail.com",
      "zhuravlikkota@gmail.com",
      "zjv.oqa@gmail.com"
    ],
    "staff": [
      "tatsuyatakabeworks@gmail.com"
    ],
    "nodes": [
      [
        "動画フォルダ",
        "1oCkUk-xVwRZB0DyoZwmcg1VbE-P4NngO"
      ],
      [
        "スライドフォルダ",
        "1edfe2SZZaYfnJjBq7sN28vX08VH5Qpmh"
      ],
      [
        "親フォルダ(未来学)",
        "1tDO4wMhXDe1AkZ0r682bTRxmoImV99e6"
      ]
    ]
  },
  "AIと社会Ⅰ": {
    "roster": [
      "aratou.t-hi@nhk.or.jp",
      "ayako.katano.0614@gmail.com",
      "boss_saiko@yahoo.co.jp",
      "cochou@gmail.com",
      "dantanyh49@gmail.com",
      "f.tomohisa26@gmail.com",
      "g2460117@edu.cc.ocha.ac.jp",
      "goutafujino1226@gmail.com",
      "handa.tsukuba@gmail.com",
      "hideaki_owa@hotmail.com",
      "hideakiowa@gmail.com",
      "honamifurugaki@gmail.com",
      "i-tomoya@mars.dti.ne.jp",
      "i.sengoku@code.or.jp",
      "ishibaa.55@gmail.com",
      "itomo2007@gmail.com",
      "jhosoisa18@gmail.com",
      "jun0307kamosida@gmail.com",
      "kaishyu.110211@gmail.com",
      "kato-hiromitsu@outlook.jp",
      "kawahara.7a@gmail.com",
      "kensato.uec@gmail.com",
      "kenuesaka@icloud.com",
      "kimiwatanabe3@gmail.com",
      "kobayuji.0909@gmail.com",
      "kosukeinoue.ki@gmail.com",
      "longvalleyriver.k516@gmail.com",
      "longvalleyriver.k516@icloud.com",
      "mayamamoto5@gmail.com",
      "meg.furush@gmail.com",
      "mockry1830@gmail.com",
      "pasuko6899@gmail.com",
      "sachi.shiraki@gmail.com",
      "sayoko.otsuka19841118@gmail.com",
      "sayoko.otsuka@mail.toyotaconnected.co.jp",
      "shirota.ichiro@gmail.com",
      "shun5crewsz@gmail.com",
      "sn7131923@gmail.com",
      "suzukimasanori@gmail.com",
      "tatsuro_handa@me.com",
      "teniwohajp@gmail.com",
      "tsumukei04@gmail.com",
      "tsumura-kei@asakonet.co.jp",
      "xiangmiao12@gmail.com",
      "yamada.sophia@gmail.com",
      "yuki.osh@gmail.com",
      "zhangqiang960517@gmail.com",
      "zhangqiang960517@outlook.com",
      "zhouaijia8@gmail.com"
    ],
    "staff": [
      "pnch.0924@gmail.com",
      "taiko.hiroaki@gmail.com"
    ],
    "nodes": [
      [
        "科目フォルダ",
        "1Ok59uWTF1ejVpvFPFIi1XVMqo5ECXgQC"
      ],
      [
        "スライドフォルダ",
        "1RQuRxYETN_IJGnAAUEKCCLatPZ2htQBS"
      ]
    ]
  },
  "技術哲学": {
    "roster": [
      "27kasairio@shibushibu.ed.jp",
      "anythingone123@gmail.com",
      "atsushi.udagawa@gmail.com",
      "bonnou108@mac.com",
      "dantanyh49@gmail.com",
      "ehlytjp@gmail.com",
      "g2460117@edu.cc.ocha.ac.jp",
      "goutafujino1226@gmail.com",
      "guangzuoyutian@gmail.com",
      "gymratsjk@gmail.com",
      "handa.tsukuba@gmail.com",
      "hideaki_owa@hotmail.com",
      "hideakiowa@gmail.com",
      "ishiishify@gmail.com",
      "itomo2007@gmail.com",
      "jun0307kamosida@gmail.com",
      "k.fujimon@gmail.com",
      "kaishyu.110211@gmail.com",
      "kaizumaki@gmail.com",
      "kato-hiromitsu@outlook.jp",
      "kenuesaka@icloud.com",
      "kojin.oshiba@gmail.com",
      "kosukeinoue.ki@gmail.com",
      "kumataro0608jp@yahoo.co.jp",
      "liu.yi@outlook.jp",
      "masahito@mri.co.jp",
      "mayamamoto5@gmail.com",
      "mockry1830@gmail.com",
      "okada@ande.ink",
      "pinksaloonrock@gmail.com",
      "rei@studio-true.net",
      "shingo.vyv03344@nifty.ne.jp",
      "shinichi.nakama@omron.com",
      "shirota.ichiro@gmail.com",
      "tatsuro_handa@me.com",
      "tatsuyatakabeworks@gmail.com",
      "tsumura-kei@asakonet.co.jp",
      "utakata.philosopher@gmail.com",
      "xiangmiao12@gmail.com",
      "ykyosuke0224@gmail.com",
      "zhangqiang960517@gmail.com",
      "zhangqiang960517@outlook.com",
      "zhouaijia8@gmail.com"
    ],
    "staff": [
      "pnch.0924@gmail.com",
      "taiko.hiroaki@gmail.com"
    ],
    "nodes": [
      [
        "科目フォルダ",
        "1AnIv_XMEyq2cinXg1CHx9TZA3WgeKMSR"
      ],
      [
        "動画フォルダ",
        "1gGXQEpg7AUgV_1xxplI08CIq02cKW57q"
      ],
      [
        "スライドフォルダ",
        "1E2GHCQe0TXdkFLGOyjVypYE5OsTQYOqm"
      ]
    ]
  }
};

var FILES = {
  "テクノロジーの未来学": [
    "1OhoOMiIq5_SRT1v6ufBb_qHfUf8r5mrR",
    "1MJRoYs3uyW5aVjmq0HVcUKIPrI_mOjEA",
    "1H6_AC_Gjek5_6MPf47FlSDBOF8IMV9ZA",
    "12fNh9bijAlPH1gsSvXsOOLt-iWkWCrYd",
    "12jVHkNlI8O2VAisHMZI3ynWLVs0Jr8C9",
    "1r8UWXoeABwyROspD54vZKXsLBwIlGD8b",
    "1MpgjZpRi_NCeMjTGRvqR17zn4YSNbs6r",
    "1qXZHTrvTb0mfIaEEmEzb8fHxy5BVQLWj",
    "1LmOfuCSCLXzPB1elrIYY2Zoeng8q6Zk-",
    "1fsCW06ct29RqP-Z_Dn20gJpLUVi7eAMJ",
    "1INmygo41qCVHIQpWzeKGM1EYQ1m-hAGj",
    "1cqVaWTJ5s_qGt5gtBTIqvuPgAhw1aXxa",
    "1Dkfw2k2yVrNYRX2g-BC1MALIsvDeIRWR",
    "1PMlBoyi6I70ISW2FPsO5xrz4ghgDO2oM",
    "1gBE83AM82JmBchbQvvAyTVyLi3myHWMV",
    "10H7xRdq822dl_7iur_xzWKAF2mLQmOrb"
  ],
  "AIと社会Ⅰ": [
    "10QUZmI8FBJybAbG3BAOdeFnZWuuHR1gK",
    "1OVLAAqay4LhA0YSb1q9SfTrV9k46c0Zd",
    "1aI4ft6m5APtco3wng98Wz9EXXDsAn5t3",
    "1mMfqQNGkKU7zmBk8NEmaPtEXCnWPEGNv",
    "1N8BHH3KSRQkYL7xxW_ftSvErxJJblt_b",
    "17CJBIORVr-E4l_NprPHlJAHepG2-TqLz",
    "1Qt6OJtl3wlUQ1tjioDZcGS1O-cgOUnBv"
  ],
  "技術哲学": [
    "1rrosDJI2FCoCbZzGtl1FKyZ4tbwJgC5Q",
    "1xEDCTRu223RNELcn5Lm7kmyniHQFwUJm",
    "1Yfnia0PCrwWE_ijsxsl0mzBIqwhxLzEn"
  ]
};

function isCorp(email) {
  var d = String(email).split('@')[1] || '';
  return CORP_DOMAINS.indexOf(d.toLowerCase()) >= 0;
}

/** 1ファイル/フォルダの閲覧可能メールを全部取る（継承分も含む） */
function aclOf(id) {
  var emails = {}, domains = [], anyone = false;
  var token = null;
  do {
    var res = Drive.Permissions.list(id, {
      fields: 'nextPageToken,permissions(id,type,role,emailAddress,domain,permissionDetails)',
      pageSize: 100, supportsAllDrives: true, useDomainAdminAccess: false, pageToken: token
    });
    (res.permissions || []).forEach(function (p) {
      if (p.type === 'anyone') anyone = true;
      else if (p.type === 'domain') domains.push(p.domain);
      else if (p.emailAddress) emails[p.emailAddress.toLowerCase()] = p.role;
    });
    token = res.nextPageToken;
  } while (token);
  return { emails: emails, domains: domains, anyone: anyone };
}

function auditAll() {
  var report = [];
  report.push(['科目', '対象', 'ID', '総人数', '受講生で見られる', '受講生で見られない', '法人', '名簿外', '一般アクセス']);
  var detail = [['科目', '対象', '区分', 'メール']];

  Object.keys(SUBJECTS).forEach(function (subj) {
    var conf = SUBJECTS[subj];
    var roster = {};
    conf.roster.forEach(function (e) { roster[e] = 1; });
    conf.staff.forEach(function (e) { roster[e] = 1; });

    var nodes = conf.nodes.slice();
    (FILES[subj] || []).forEach(function (fid) {
      var nm = '(file)';
      try { nm = Drive.Files.get(fid, {fields: 'name', supportsAllDrives: true}).name; } catch (e) {}
      nodes.push([nm, fid]);
    });

    nodes.forEach(function (nd) {
      var label = nd[0], id = nd[1];
      var a;
      try { a = aclOf(id); } catch (e) { report.push([subj, label, id, 'ERR: ' + e, '', '', '', '', '']); return; }
      var have = Object.keys(a.emails);
      var ok = [], corp = [], extra = [];
      have.forEach(function (e) {
        if (roster[e]) ok.push(e);
        else if (isCorp(e)) corp.push(e);
        else extra.push(e);
      });
      var missing = Object.keys(roster).filter(function (e) { return !a.emails[e]; });

      report.push([subj, label, id, have.length, ok.length, missing.length, corp.length, extra.length,
                   a.anyone ? '⚠ リンクを知る全員' : (a.domains.length ? 'ドメイン:' + a.domains.join(',') : '制限付き')]);

      missing.forEach(function (e) { detail.push([subj, label, '❌ 見られない（要付与）', e]); });
      extra.forEach(function (e) { detail.push([subj, label, '⚠ 名簿外（未受講の可能性）', e]); });

      Logger.log('[' + subj + '] ' + label + ' → 計' + have.length +
                 ' / 受講生OK ' + ok.length + ' / 不足 ' + missing.length +
                 ' / 法人 ' + corp.length + ' / 名簿外 ' + extra.length +
                 ' / ' + (a.anyone ? 'ANYONE!' : '制限付き'));
    });
  });

  var ss = SpreadsheetApp.create('mU権限監査 ' + Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy-MM-dd HH:mm'));
  var s1 = ss.getActiveSheet(); s1.setName('サマリー');
  s1.getRange(1, 1, report.length, report[0].length).setValues(report);
  var s2 = ss.insertSheet('明細');
  s2.getRange(1, 1, detail.length, detail[0].length).setValues(detail);
  Logger.log('=== 監査結果: ' + ss.getUrl() + ' ===');
}

/** 不足分だけを付与する（監査で内容を確認してから実行すること） */
function grantMissing() {
  Object.keys(SUBJECTS).forEach(function (subj) {
    var conf = SUBJECTS[subj];
    var want = conf.roster.concat(conf.staff);
    var folderId = conf.nodes[0][1];  // 科目のトップ（配下に継承させる）
    var a = aclOf(folderId);
    var added = 0;
    want.forEach(function (e) {
      if (a.emails[e]) return;
      try {
        Drive.Permissions.create({type: 'user', role: 'reader', emailAddress: e}, folderId,
          {sendNotificationEmail: false, supportsAllDrives: true});
        added++;
      } catch (err) { Logger.log('  [ERR] ' + subj + ' ' + e + ' : ' + err); }
    });
    Logger.log('[' + subj + '] ' + conf.nodes[0][0] + ' に ' + added + ' 名を追加');
  });
}

// ============================================================
// 追加：閲覧者のダウンロード／コピー／印刷を不可にする（setNoDownloadAll）
// ============================================================

var FILE_IDS = [
  // テクノロジーの未来学
  '1OhoOMiIq5_SRT1v6ufBb_qHfUf8r5mrR', // 1 動画
  '1MJRoYs3uyW5aVjmq0HVcUKIPrI_mOjEA', // 1 スライド（松島倫明）
  '1H6_AC_Gjek5_6MPf47FlSDBOF8IMV9ZA', // 2 動画
  '12fNh9bijAlPH1gsSvXsOOLt-iWkWCrYd', // 2 スライド（梶谷健人）
  '12jVHkNlI8O2VAisHMZI3ynWLVs0Jr8C9', // 3 動画
  '1r8UWXoeABwyROspD54vZKXsLBwIlGD8b', // 3 スライド（高口康太）
  '1MpgjZpRi_NCeMjTGRvqR17zn4YSNbs6r', // 4 動画
  '1qXZHTrvTb0mfIaEEmEzb8fHxy5BVQLWj', // 4 スライド（守慎哉）
  '1LmOfuCSCLXzPB1elrIYY2Zoeng8q6Zk-', // 5 動画
  '1fsCW06ct29RqP-Z_Dn20gJpLUVi7eAMJ', // 5 スライド（藤井直敬）
  '1INmygo41qCVHIQpWzeKGM1EYQ1m-hAGj', // 6 動画
  '1cqVaWTJ5s_qGt5gtBTIqvuPgAhw1aXxa', // 6 スライド（若山照彦）
  '1Dkfw2k2yVrNYRX2g-BC1MALIsvDeIRWR', // 7 動画
  '1PMlBoyi6I70ISW2FPsO5xrz4ghgDO2oM', // 7 スライド（池上高志）
  '1gBE83AM82JmBchbQvvAyTVyLi3myHWMV', // 8 動画
  '10H7xRdq822dl_7iur_xzWKAF2mLQmOrb', // 8 スライド（総論）
  // AIと社会Ⅰ
  '10QUZmI8FBJybAbG3BAOdeFnZWuuHR1gK', // 1 動画
  '1OVLAAqay4LhA0YSb1q9SfTrV9k46c0Zd', // 2 動画
  '1aI4ft6m5APtco3wng98Wz9EXXDsAn5t3', // 2 スライド①
  '1mMfqQNGkKU7zmBk8NEmaPtEXCnWPEGNv', // 2 スライド②
  '1N8BHH3KSRQkYL7xxW_ftSvErxJJblt_b', // 3 動画
  '17CJBIORVr-E4l_NprPHlJAHepG2-TqLz', // 3 スライド（柳平大樹）
  '1Qt6OJtl3wlUQ1tjioDZcGS1O-cgOUnBv', // 4 動画
  // 技術哲学
  '1rrosDJI2FCoCbZzGtl1FKyZ4tbwJgC5Q', // 1 動画
  '1xEDCTRu223RNELcn5Lm7kmyniHQFwUJm', // 2 動画
  '1Yfnia0PCrwWE_ijsxsl0mzBIqwhxLzEn'  // 2 スライド（直江清隆）
];

function setNoDownloadAll() {
  var ok = 0, skip = 0, ng = 0;
  for (var i = 0; i < FILE_IDS.length; i++) {
    var id = FILE_IDS[i];
    try {
      var f = Drive.Files.get(id, { fields: 'id,name,copyRequiresWriterPermission', supportsAllDrives: true });
      if (f.copyRequiresWriterPermission === true) {
        Logger.log('[skip] 既に不可: ' + f.name);
        skip++;
        continue;
      }
      Drive.Files.update({ copyRequiresWriterPermission: true }, id, null, { supportsAllDrives: true });
      var v = Drive.Files.get(id, { fields: 'name,copyRequiresWriterPermission', supportsAllDrives: true });
      Logger.log('[' + (v.copyRequiresWriterPermission ? 'OK' : 'FAIL') + '] ' + v.name);
      v.copyRequiresWriterPermission ? ok++ : ng++;
    } catch (e) {
      Logger.log('[ERR] ' + id + ' : ' + e);
      ng++;
    }
  }
  Logger.log('--- 完了: 設定 ' + ok + ' / 既存 ' + skip + ' / 失敗 ' + ng + ' （全 ' + FILE_IDS.length + ' 件） ---');
}

/** 設定確認だけしたいとき */
function checkAll() {
  for (var i = 0; i < FILE_IDS.length; i++) {
    var f = Drive.Files.get(FILE_IDS[i], { fields: 'name,copyRequiresWriterPermission', supportsAllDrives: true });
    Logger.log((f.copyRequiresWriterPermission ? 'DL不可 ' : 'DL可   ') + f.name);
  }
}
