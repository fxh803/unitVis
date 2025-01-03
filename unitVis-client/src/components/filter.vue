<script setup>
import EventBus from "@/EventBus";
import globalData from "@/globalData";
import { ElMessage } from 'element-plus'
</script>
<template>
  <div v-if="filterType()" class="filter-container">

    <el-input v-if="filterType() == 'number'" class="filter-input" v-model="filter1Input" placeholder="Please input"
      @input="handleFilter1Input()" :disabled="filter1InputDisable">
      <template #prepend>
        <el-select v-model="filter1Select" placeholder="filter" class="filter-select" @change="handlefilter1Select()">
          <el-option label="ALL" value="ALL" />
          <el-option label=">=" value=">=" />
          <el-option label="<=" value="<=" />
        </el-select>
      </template>
    </el-input>

    <el-select v-if="filterType() == 'string'" v-model="filter2Select" placeholder="selectYourData"
      class="filter-select2" @change="handlefilter2Select()">
      <el-option v-for="item in stringOption()" :key="item.value" :label="item.label" :value="item.value" />
    </el-select>
  </div>
</template>

<script>
export default {
  name: 'filterComponent',
  props: {
    lineId: {
      type: Number
    }
  },
  data() {
    return {
      assignId: null,
      filter1Input: null,
      filter1Select: null,
      filter2Select: null,
      filter1InputDisable: false
    };
  },
  mounted() {
    //初始化
    if (globalData.filteredData[this.lineId]) {
      this.filter1Input = globalData.filteredData[this.lineId]['filter1Input'];
      this.filter1Select = globalData.filteredData[this.lineId]['filter1Select']
      this.filter2Select = globalData.filteredData[this.lineId]['filter2Select']
    }
  },
  methods: {
    isNumeric(value) {
      return !isNaN(parseFloat(value)) && isFinite(value);
    },
    //判断选择的数据是不是数字
    filterType() {
      const item = globalData.lineDetail.find(item => item.lineId === this.lineId);
      if (item) {
        this.assignId = item['assignId']
      }
      const firstItem = globalData.table_data[0];
      if (globalData.mappingData[this.assignId]?.option) {
        const option = globalData.mappingData[this.assignId].option
        if (this.isNumeric(firstItem[option])) {
          return 'number';
        }
        else {
          return 'string';
        }
      }

      return null;

    },
    stringOption() {
      //找到assignID先
      this.assignId = globalData.lineDetail.find(item => item.lineId === this.lineId)['assignId']

      const item = globalData.emitDetail.find(detail => detail.assignId === this.assignId);
      const optionsValue = Array.from(new Set(item['selectedData']));
      let options = [];

      if (optionsValue.length > 1) {
        options.push({ value: 'ALL', label: 'ALL' });
        optionsValue.forEach(optionValue => {
          options.push({ value: optionValue, label: optionValue });
        });
      }
      else {
        options.push({ value: 'ALL', label: 'ALL' });
      }


      return options;
    },
    handlefilter1Select() {
      this.updateData();
    },
    handleFilter1Input() {
      //数字限制
      this.filter1Input = this.filter1Input.replace(/\D/g, '') * 1;
      console.log(this.filter1Input)
      this.updateData();
    },
    handlefilter2Select() {
      this.updateData();
    },
    updateData() {
      //更新filteredData
      if (!globalData.filteredData[this.lineId]) {
        // 如果不存在，初始化为一个空对象
        globalData.filteredData[this.lineId] = {};
      }
      // if (!(this.filter1Input) && this.filter1Input != 0) {
      //   this.filter1Input = null;
      // }
      // if (!this.filter1Select) {
      //   this.filter1Select = null;
      // }
      // if (!this.filter2Select) {
      //   this.filter2Select = null;
      // }
      globalData.filteredData[this.lineId]['filter2Select'] = this.filter2Select;
      globalData.filteredData[this.lineId]['filter1Select'] = this.filter1Select;
      globalData.filteredData[this.lineId]['filter1Input'] = this.filter1Input;

      const assignId = globalData.lineDetail.find(detail => detail.lineId === this.lineId)['assignId']
      const mappedData = globalData.emitDetail.find(detail => detail.assignId === assignId)['selectedData']
      console.log(this.filter1Input, this.filter1Select)
      if (this.filter1Select) {
        let result = [];
        //选择了all就直接传递
        if (this.filter1Select === 'ALL') {
          result = mappedData;
        }
        else {

          if (this.filter1Select === '>=' && this.filter1Input != null) {
            result = mappedData
              .map(num => Number(num))  // 将字符串转换为数字
              .filter(num => num >= this.filter1Input);  // 过滤数字
          }
          else if (this.filter1Select === '<=' && this.filter1Input != null) {
            result = mappedData
              .map(num => Number(num))  // 将字符串转换为数字
              .filter(num => num <= this.filter1Input);  // 过滤数字
          }
        }



        console.log(result)
        globalData.lineDetail.find(detail => detail.lineId === this.lineId)['filteredData'] = result

      }
      if (this.filter2Select) {
        if (this.filter2Select != 'ALL')
          globalData.lineDetail.find(detail => detail.lineId === this.lineId)['filteredData'] = mappedData.filter(element => element === this.filter2Select);
        else
          globalData.lineDetail.find(detail => detail.lineId === this.lineId)['filteredData'] = mappedData;
      }
    }
  },
  watch: {
    filter1Select: {
      handler(newVal) {
        if (newVal == "ALL") {
          this.filter1InputDisable = true;
        }
        else {
          this.filter1InputDisable = false;
        }
      }
    }
  }
}
</script>

<style>
@import '../assets/css/filter.css';
</style>