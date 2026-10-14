/**
 * mU Vimeo版アーカイブ用：講義スライドを「リンクを知っている全員（閲覧者）」にする
 *
 * Vimeo組の受講生はGoogleアカウントを持っていないため、Vimeo版ページ（vimeo-*.html）の
 * スライドリンクは限定公開リンク（リンクを知っている全員が閲覧可）で開けるようにする。
 * 既存の個別共有・ダウンロード不可設定はそのまま残る。
 *
 * 使い方：script.google.com で新規プロジェクト → 貼り付け → サービス＋で Drive API を追加 → setLinkSharingAll を実行
 * 対象：data/subjects.json の slides の全Drive ID（20件）
 */

var FILE_IDS = [
  '1MJRoYs3uyW5aVjmq0HVcUKIPrI_mOjEA', // テクノロジーの未来学 1 講義スライド（松島倫明）
  '12fNh9bijAlPH1gsSvXsOOLt-iWkWCrYd', // テクノロジーの未来学 2 講義スライド（梶谷健人）
  '1r8UWXoeABwyROspD54vZKXsLBwIlGD8b', // テクノロジーの未来学 3 講義スライド（高口康太）
  '1qXZHTrvTb0mfIaEEmEzb8fHxy5BVQLWj', // テクノロジーの未来学 4 講義スライド（守慎哉）
  '1fsCW06ct29RqP-Z_Dn20gJpLUVi7eAMJ', // テクノロジーの未来学 5 講義スライド（藤井直敬）
  '1cqVaWTJ5s_qGt5gtBTIqvuPgAhw1aXxa', // テクノロジーの未来学 6 講義スライド（若山照彦）
  '1PMlBoyi6I70ISW2FPsO5xrz4ghgDO2oM', // テクノロジーの未来学 7 講義スライド（池上高志）
  '10H7xRdq822dl_7iur_xzWKAF2mLQmOrb', // テクノロジーの未来学 8 講義スライド（総論）
  '1aI4ft6m5APtco3wng98Wz9EXXDsAn5t3', // AIと社会Ⅰ 2 講義スライド①
  '1mMfqQNGkKU7zmBk8NEmaPtEXCnWPEGNv', // AIと社会Ⅰ 2 講義スライド②
  '17CJBIORVr-E4l_NprPHlJAHepG2-TqLz', // AIと社会Ⅰ 3 講義スライド（柳平大樹）
  '1Yfnia0PCrwWE_ijsxsl0mzBIqwhxLzEn', // 技術哲学 2 講義スライド（直江清隆）
  '1WWVIdBWQcd9GYTlR-nOZyPsiQhAFb_MI', // 技術哲学 3 講義スライド（岡田悠汰）
  '1hGASLXnVQ7CNAM99NNdQj85FE7-eyifD', // 技術哲学 4 講義スライド（村田純一）
  '1DSi8kxgK34BFd0ExvkHfHU3mL_nvn-S8', // 技術哲学 7 講義スライド（染谷昌義）
  '16e3Buqk09YuvFktHG6BjS12qlGyLWn6Z', // 技術哲学 8 講義スライド（原島大輔）
  '1J4DxSuZ0_LaSsehtq0RJkqlcYoEzfWu9', // 技術史 2 講義スライド（島田将喜）
  '1WtATfwa7yPzeypWcKnrz9iJU9ve57D82MtVTRJ9XgU0', // 技術史 3 講義スライド（相馬皓介）
  '1pz4rwhkd3nkJB1BySjtULBr2sXjaVGpK', // 技術史 5 講義スライド（小島孝夫）
  '1Vl9S8-0vZnDxo-Yxo8mbj-eWD2B1SdSe', // 技術史 5 講義資料：素潜り潜水漁業者の生涯漁獲量・漁獲額（Excel）
];

function setLinkSharingAll() {
  var ok = 0, ng = 0;
  FILE_IDS.forEach(function (id) {
    try {
      if (Drive.Permissions.create) {
        Drive.Permissions.create({type: 'anyone', role: 'reader', allowFileDiscovery: false}, id, {supportsAllDrives: true});
      } else {
        Drive.Permissions.insert({type: 'anyone', role: 'reader', withLink: true}, id, {supportsAllDrives: true});
      }
      Logger.log('OK  ' + id + '  ' + DriveApp.getFileById(id).getName());
      ok++;
    } catch (e) {
      Logger.log('NG  ' + id + '  ' + e.message);
      ng++;
    }
  });
  Logger.log('完了：成功 ' + ok + ' 件／失敗 ' + ng + ' 件');
}
