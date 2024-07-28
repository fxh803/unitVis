let data_prepared = false;
let table_data = [];
const dropZone = document.getElementById("drop-zone");
const tableBodyWrapper = document.querySelector(".table-body-wrapper");
const tableHead = document.querySelector(".table-head");
window.onload = function () {
  toggleCsv(0);
};

function pushData() {
  // 获取第一个对象作为参考，提取其所有键作为表格的列
  const firstItem = table_data[0];
  const keys = Object.keys(firstItem);

  keys.forEach((key)=>{
    const text = document.createElement("text");
    text.textContent = key;
    tableHead.appendChild(text);
  })


  //循环渲染
  table_data.forEach((item, index) => {
    const tableItem = document.createElement("div");
    tableItem.classList.add("table-item");
    tableItem.setAttribute("index", index);
    if (index % 2 != 0) {
      tableItem.style.backgroundColor = "#bdd7ee";
    } else {
      tableItem.style.backgroundColor = "#ffffff";
    }

    const indexText = document.createElement("text");
    indexText.textContent = index;
    tableItem.appendChild(indexText);

    keys.forEach((key)=>{
      const text = document.createElement("text");
      text.textContent = item[key];
      tableItem.appendChild(text);
    })
    tableBodyWrapper.appendChild(tableItem);
  });
}

dropZone.addEventListener("dragover", function (e) {
  e.preventDefault();
  dropZone.style.backgroundColor = "#f0f0f0";
});

dropZone.addEventListener("dragleave", function () {
  dropZone.style.backgroundColor = "white";
});

dropZone.addEventListener("drop", function (e) {
  e.preventDefault();
  dropZone.style.backgroundColor = "white";

  const file = e.dataTransfer.files[0];
  const reader = new FileReader();

  reader.onload = function (event) {
    const csv = event.target.result;
    const lines = csv.split("\n");
    const headers = lines[0].trim().split(",");

    const data = [];
    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].trim().split(",");
      const entry = {};
      for (let j = 0; j < headers.length; j++) {
        entry[headers[j]] = values[j];
      }
      data.push(entry);
    }

    table_data = data
    //执行操作
    pushData();
    toggleCsv(1);
  };

  reader.readAsText(file);

  
});

function toggleCsv(status) {
  const dropZone = document.getElementById("drop-zone");
  const customTable = document.getElementById("custom-table");
  if (status === 0) {
    dropZone.style.display = "flex";
    customTable.style.display = "none";
  } else {
    dropZone.style.display = "none";
    customTable.style.display = "flex";
  }
}
