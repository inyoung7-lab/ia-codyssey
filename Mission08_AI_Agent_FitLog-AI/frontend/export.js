"use strict";
function workoutCSV(records) {
  const field = value => {
    let text = String(value);
    // Prevent spreadsheet formulas in user-entered memo fields.
    if (/^[\s]*[=+\-@]/.test(text) || /^[\t\r\n]/.test(text)) text = "'" + text;
    return '"' + text.replace(/"/g, '""') + '"';
  };
  const rows = [...records].sort((a, b) => a.date.localeCompare(b.date));
  return "\uFEFFdate,value,memo\r\n" + rows.map(row => [row.date, row.value, row.memo].map(field).join(",")).join("\r\n") + (rows.length ? "\r\n" : "");
}
element("csv-download").addEventListener("click", () => {
  if (dataLoading || dataSaving || !dataRecords.length) return;
  let url;
  try {
    const blob = new Blob([workoutCSV(dataRecords)], {type:"text/csv;charset=utf-8"});
    url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const now = new Date();
    const day = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,"0")}-${String(now.getDate()).padStart(2,"0")}`;
    link.href = url; link.download = `fitlog-data-${day}.csv`;
    document.body.append(link); link.click(); link.remove();
    status("export-status", `${dataRecords.length}개 기록의 CSV 다운로드를 시작했습니다.`);
  } catch { status("export-status", "다운로드를 시작하지 못했습니다. 다시 시도해 주세요.", true); }
  finally { if (url) setTimeout(() => URL.revokeObjectURL(url), 1000); }
});
