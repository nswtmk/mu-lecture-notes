/**
 * mU配信素材：閲覧者のダウンロード／コピー／印刷を一括で不可にする
 *
 * 使い方
 *  1. https://script.google.com/home/projects/create を開く
 *  2. このファイルの中身を全部貼り付けて保存
 *  3. 左メニュー「サービス」＋ → Drive API → 追加（識別子は Drive のまま）
 *  4. setNoDownloadAll を選んで「実行」→ 初回だけ承認ダイアログで許可
 *  5. 実行ログに 1件ずつ結果が出る
 *
 * subjects.json の video / slides の全IDを対象にしている（2026-08-22時点・全26件）。
 */

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
