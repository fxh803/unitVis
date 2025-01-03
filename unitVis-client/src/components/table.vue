<script setup>
import EventBus from "@/EventBus";
import globalData from "@/globalData";
import { ElMessage } from 'element-plus'; 
</script>
<template>
  <div class="table-container">
    <el-button v-if="showTable && !globalData.collaging" class="deleteTable" type="danger" icon="Close"
      @click="deleteTable" />
    <div v-if="!showTable" class="drop-zone" id="drop-zone" @dragover.prevent="handleCsvDragOver"
      @dragleave="handleCsvDragLeave" @drop.prevent="handleCsvDrop" @click="uploadCsvClick"
      @mouseover="handleCsvDragOver" @mouseleave="handleCsvDragLeave">Drop CSV File Here
      <input type="file" class="fileInput" id="csvInput" accept=".csv" @change="uploadCsvChange">
    </div>
    <div v-if="showTable" class="custom-table" id="custom-table">
      <div class="table-head">
        <div v-for="(key, index) in showkeys" :key="index" class="table-head-div"
          @mouseover="handleTableHeadDivMouseOver($event, key)" @mouseleave="handleTableHeadDivMouseLeave($event, key)">
          {{ key }}
        </div>

        <div v-show="showDropdown" id="table-head-select" class="table-head-select select"
          @mouseleave="handleSelectDivMouseLeave($event, key)">
          <div class="table-head-select-wrapper select">
            <div class="table-head-select-div select" v-for="(key, index) in unshownKeys" :key="index"
              @mouseleave="handleSelectDivMouseLeave($event, key)" @click="handleSelectDivClick($event, key)">
              <el-tooltip class="item-tooltip" effect="dark" :content=key placement="left">
                {{ key }}
              </el-tooltip>
            </div>
          </div>
        </div>
      </div>
      <div class="table-body">
        <div class="table-body-wrapper">
          <div v-for="(item, index) in globalData.table_data" :key="index" class="table-item">

            <div class="table-data" v-for="key in showkeys" :key="key" :data-key="key">
              <el-tooltip class="item-tooltip" effect="dark" placement="left">
                <template #content>
                <div style="max-width: 200px;">
                  {{ item[key] }}
                </div>
              </template>
                {{
                  item[key]
                }}
              </el-tooltip>
              <img class="table-img"
                v-show="data?.option == key && data?.from <= index + 1 && data?.to >= index + 1 && filterState(data, item[key])"
                v-for="data in globalData.mappingData" :src="data?.img" alt="Image" />
            </div>

          </div>
        </div>
      </div>
    </div>


  </div>

</template>

<script>
export default {
  name: "tableComponent",
  data() {
    return {
      showTable: false,
      targetKey: "",
      theKeyWantChange: "",
      allkeys: [],
      showkeys: [],
      unshownKeys: [],
      showDropdown: false,
    };
  },
  mounted() {
  },

  methods: {
    uploadCsvClick() {
      document.getElementById('csvInput').click();
    },
    uploadCsvChange(event) {
      const file = event.target.files[0];
      event.target.style.backgroundColor = "white";
      this.processCsv(file);
    },
    deleteTable() {
      this.showTable = false;
      globalData.table_data = [];
      globalData.mappingData = {};
      globalData.filteredData = {};
      //删除映射的数据
      globalData.emitDetail.forEach(item => {
        delete item.selectedData;
      });
      //删除映射的数据
      globalData.lineDetail.forEach(item => {
        delete item.filteredData;
      });
      this.targetKey = "";
      this.theKeyWantChange = "";
      this.allkeys = [];
      this.showkeys = [];
      this.unshownKeys = [];
      this.showDropdown = false;
    },
    filterState(data, item) {
      if (data['filterOption'] && data['filter1Input']) {
        if (data['filterOption'] == '>=' && item < data['filter1Input']) {
          return false;
        }
        else if (data['filterOption'] == '<=' && item > data['filter1Input']) {
          return false;
        }
      }
      else if (data['filterOption'] && data['filter2Select']) {
        if (item != data['filter2Select']) {
          return false;
        }
      }
      return true;
    },
    handleCsvDragOver(e) {
      e.preventDefault();
      e.target.style.backgroundColor = "#f0f0f0";
    },
    handleCsvDragLeave(e) {
      e.target.style.backgroundColor = "white";
    },
    replaceCommas(input) {
      return input.replace(/"([^"]*?)"/g, (match) => {
        return match.replace(/,/g, '、');
      });
    },
    handleCsvDrop(e) {
      e.preventDefault();
      e.target.style.backgroundColor = "white";
      const file = e.dataTransfer.files[0];
      this.processCsv(file);
    },
    processCsv(file) {
      if (file.name.endsWith('.csv')) {
        const reader = new FileReader();
        reader.onload = (event) => {
          const csv = event.target.result;
          const lines = csv.split("\n");
          const headers = lines[0].trim().split(",");

          const data = [];
          const numRows = Math.min(150, lines.length - 2);
          for (let i = 1; i <= numRows; i++) {
            const values = this.replaceCommas(lines[i].trim()).split(",");
            const entry = {};
            for (let j = 0; j < headers.length; j++) {
              entry[headers[j]] = values[j];
            }
            data.push(entry);
          }
          globalData.table_data = data;
          this.pushData();
          this.showTable = true;
        };

        reader.readAsText(file);

      }
      else {
        ElMessage({
          message: " please input csv file !",
          grouping: true,
          type: 'warning',
        })
      }
    },
   
    pushData() {
      // 获取第一个对象作为参考，提取其所有键作为表格的列
      const firstItem = globalData.table_data[0];
      this.allkeys = Object.keys(firstItem);
      // 计算三种键
      if (this.allkeys.length > 6) this.showkeys = this.allkeys.slice(0, 6);
      else this.showkeys = this.allkeys;

      this.unshownKeys = this.allkeys.filter(
        (key) => !this.showkeys.includes(key)
      );
    },

    handleTableHeadDivMouseOver(event, key) {
      const parentRect = event.target.parentElement.getBoundingClientRect();
      const boundingRect = event.target.getBoundingClientRect();
      const left = boundingRect.left - parentRect.left;
      this.theKeyWantChange = key;
      if (this.unshownKeys.length > 0)
        this.showDropdown = true;
      document.querySelector(".table-head-select").style.left = left + "px";
    },
    handleTableHeadDivMouseLeave(event, key) {

      const relatedTarget = event.relatedTarget;
      if (!relatedTarget.classList.contains("select")) {
        this.showDropdown = false;
      }

    },

    handleSelectDivMouseLeave(event, key) {
      const relatedTarget = event.relatedTarget;
      if (!relatedTarget.classList.contains("select")) {

        this.showDropdown = false;
      }
    },
    handleSelectDivClick(event, key) {
      const originKey = this.theKeyWantChange;
      const targetKey = key;
      // 在 showkeys 中查找 value1 的索引
      const index1 = this.showkeys.indexOf(originKey);
      // 在 unshownKeys 中查找 value2 的索引
      const index2 = this.unshownKeys.indexOf(targetKey);
      // 交换元素
      if (index1 > -1 && index2 > -1) {
        [this.showkeys[index1], this.unshownKeys[index2]] = [
          this.unshownKeys[index2],
          this.showkeys[index1],
        ];
      }
      this.theKeyWantChange = targetKey;
    }

  },
};
</script>

<style>
@import "../assets/css/table.css";
</style>
