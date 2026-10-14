/**
 * mU講義スライドを2系統に分ける（2026-10-14 七沢さん指示）
 *
 *   Google版（Google Sites配信・index.html系）＝原本。登録したGoogleアカウントだけが見られる（科目ごとの個別共有を維持）
 *   Vimeo版（vimeo*.html）＝フォルダ「mU講義スライド（Vimeo版・リンクを知っている全員）」の複製。ログイン不要
 *
 * 使い方：script.google.com で新規プロジェクト → 貼り付け → サービス＋で Drive API を追加
 *   1) step1_openCopies を実行（複製を「リンクを知っている全員・閲覧者」に。ダウンロード可否は原本に合わせる）
 *   2) Vimeo版サイトを複製IDで公開したあと、step2_restrictOriginals を実行（原本から「リンクを知っている全員」を外す）
 */

var PAIRS = [ // [原本ID, Vimeo版複製ID]
  ['1MJRoYs3uyW5aVjmq0HVcUKIPrI_mOjEA', '1cVJt_RwXiRIfkvGJ_Lz2OjEcahN6BNbE'],
  ['12fNh9bijAlPH1gsSvXsOOLt-iWkWCrYd', '1v6D9fV92K1FkEJeUIQPdeGdhrnmFBiSl'],
  ['1r8UWXoeABwyROspD54vZKXsLBwIlGD8b', '1voYEIQeVDgjnk3i9FXpjSj33WF32H4sp'],
  ['1qXZHTrvTb0mfIaEEmEzb8fHxy5BVQLWj', '179-yhL9BZb1OhkPtfAat0rxcyxyPk9Sg'],
  ['1fsCW06ct29RqP-Z_Dn20gJpLUVi7eAMJ', '1_Z7N9kXeN9QXftNbJTpJXI577GW9t_1B'],
  ['1cqVaWTJ5s_qGt5gtBTIqvuPgAhw1aXxa', '1u6pIXFfcIlMmKKfsqobfL3eoppAGYkQt'],
  ['1PMlBoyi6I70ISW2FPsO5xrz4ghgDO2oM', '1pC5zanIngNMmS75PqqnSt8OgNGUxZT3W'],
  ['10H7xRdq822dl_7iur_xzWKAF2mLQmOrb', '1SPe8Gsadlp8No03uCGBwlBL87VYJ-dFf'],
  ['1aI4ft6m5APtco3wng98Wz9EXXDsAn5t3', '1RswNtny4W18MsVe-yBw5ZFio37_H8PkV'],
  ['1mMfqQNGkKU7zmBk8NEmaPtEXCnWPEGNv', '1kt-CuLFIR7yM_gl0brtize2I_CskOxw_'],
  ['17CJBIORVr-E4l_NprPHlJAHepG2-TqLz', '1f_-_BkZzcigdgxpOsNlIYiD3SyfEB4EB'],
  ['1Yfnia0PCrwWE_ijsxsl0mzBIqwhxLzEn', '1CbFFIxWnTN5YJTak5sYvhm3ziP3b06vK'],
  ['1WWVIdBWQcd9GYTlR-nOZyPsiQhAFb_MI', '1YPcXw9EuAyCSEBLeQX_uAMQeo4ugshN4'],
  ['1hGASLXnVQ7CNAM99NNdQj85FE7-eyifD', '1l_wPlN16BU6So-Dta5PqnWdXplsHT0Sk'],
  ['1DSi8kxgK34BFd0ExvkHfHU3mL_nvn-S8', '1M7gzVHqum3beq_JGmMJ9Mgef0EsiUndg'],
  ['16e3Buqk09YuvFktHG6BjS12qlGyLWn6Z', '1wlWt_dKOIHloHfUBtkMekGp2XRi8S4Hv'],
  ['1J4DxSuZ0_LaSsehtq0RJkqlcYoEzfWu9', '1gGyOV97JJ7PWVw1UG4F-TFjXPvTGFM8V'],
  ['1WtATfwa7yPzeypWcKnrz9iJU9ve57D82MtVTRJ9XgU0', '1k_cYPqiOU8ZwVaRQ0w34w02QjgF7JAnZqapklzW3-J4'],
  ['1pz4rwhkd3nkJB1BySjtULBr2sXjaVGpK', '1miQjJddvAJuqrlft06Vm8_ABuLDXh_x1'],
  ['1Vl9S8-0vZnDxo-Yxo8mbj-eWD2B1SdSe', '1AXhmlusPOvX2hzu5lr7j6zKV72VLhSzQ']
];

function step1_openCopies() {
  var ok = 0, ng = 0;
  PAIRS.forEach(function (p) {
    try {
      var orig = Drive.Files.get(p[0], {fields: 'copyRequiresWriterPermission', supportsAllDrives: true});
      Drive.Files.update({copyRequiresWriterPermission: !!orig.copyRequiresWriterPermission}, p[1], null, {supportsAllDrives: true});
      Drive.Permissions.create({type: 'anyone', role: 'reader', allowFileDiscovery: false}, p[1], {supportsAllDrives: true});
      Logger.log('OK  ' + p[1] + '  DL不可=' + !!orig.copyRequiresWriterPermission + '  ' + DriveApp.getFileById(p[1]).getName());
      ok++;
    } catch (e) { Logger.log('NG  ' + p[1] + '  ' + e.message); ng++; }
  });
  Logger.log('step1 完了：成功 ' + ok + ' 件／失敗 ' + ng + ' 件');
}

function step2_restrictOriginals() {
  var ok = 0, ng = 0;
  PAIRS.forEach(function (p) {
    try {
      Drive.Permissions.remove(p[0], 'anyoneWithLink', {supportsAllDrives: true});
      Logger.log('OK  ' + p[0] + '  ' + DriveApp.getFileById(p[0]).getName());
      ok++;
    } catch (e) { Logger.log('NG  ' + p[0] + '  ' + e.message); ng++; }
  });
  Logger.log('step2 完了：成功 ' + ok + ' 件／失敗 ' + ng + ' 件');
}
