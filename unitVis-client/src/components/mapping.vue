<script setup>
import EventBus from "@/EventBus";
import globalData from "@/globalData";
import { ArrowDown } from '@element-plus/icons-vue'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
</script>
<template>
    <div class="mapping-container">
        <div class="dataOption">
            <el-select class="column-select" v-model="selectedDataOption" placeholder="data" size="small"
                :empty-values="[null, undefined]" :value-on-clear="null" clearable @change="handleDataChange()">
                <el-option v-for="item in dataOption" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
            <div v-if="selectedDataOption" class="row-select">
                <el-input class="el-input" v-model="from" placeholder="from" size="small" autocomplete="off"
                    @input="fromInput()" @change="fromInputChange()" />
                -
                <el-input class="el-input" v-model="to" placeholder="to" size="small" autocomplete="off"
                    @input="toInput()" @change="toInputChange()" />
            </div>
        </div>
        <div class="filterOption">
            <el-select class="filter-select" v-model="selectedFilterOption" placeholder="filter" size="small"
                :empty-values="[null, undefined]" :value-on-clear="null" clearable @change="handleFilterChange()">
                <el-option v-for="item in filterOption()" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>

            <el-input v-if="filterOption()?.length > 1 && selectedFilterOption" class="el-input" v-model="filter1Input"
                placeholder="" size="small" autocomplete="off" @input="handleFilter1Input()" />

            <el-select v-if="filterOption()?.length == 1 && selectedFilterOption" class="filter-data-select"
                v-model="filter2Select" placeholder="" size="small" :empty-values="[null, undefined]"
                :value-on-clear="null" @change="handleFilter2SelectChange()">
                <el-option v-for="item in filter2SelectOption()" :key="item.value" :label="item.label"
                    :value="item.value" />
            </el-select>
        </div>
        <div class="visOption">
            <el-select v-model="selectedVisOption" placeholder="visualization" size="small"
                :empty-values="[null, undefined]" :value-on-clear="null" clearable @change="handleVisChange()">
                <el-option v-for="item in visOption()" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
        </div>
    </div>

</template>

<script>
export default {
    name: 'mappingComponent',
    props: {
        assignId: {
            type: Number,
        },
    },
    data() {
        return {
            dataOption: [],
            selectedDataOption: null,
            selectedVisOption: null,
            selectedFilterOption: null,
            filter2Select: null,
            from: 0,
            to: 0,
            filter1Input: 0,
            dataLength: 0,
        };
    },
    mounted() {
        console.log(this.assignId)
        const firstItem = globalData.table_data[0];
        console.log(firstItem)
        const keys = Object.keys(firstItem);
        keys.forEach(key => {
            this.dataOption.push({ value: key, label: key })
        });
        this.dataLength = globalData.table_data.length;
        //初始化
        if (globalData.mappingData[this.assignId]) {
            this.from = globalData.mappingData[this.assignId]['from'];
            this.to = globalData.mappingData[this.assignId]['to'];
            this.selectedDataOption = globalData.mappingData[this.assignId]['option'];
            this.selectedVisOption = globalData.mappingData[this.assignId]['vis'];
            this.selectedFilterOption = globalData.mappingData[this.assignId]['filterOption'];
            this.filter1Input = globalData.mappingData[this.assignId]['filter1Input'];
            this.filter2Select = globalData.mappingData[this.assignId]['filter2Select'];
        }

    },
    methods: {
        isNumeric(value) {
            return !isNaN(parseFloat(value)) && isFinite(value);
        },
        //判断选择的数据是不是数字，不是的不能选择大小
        visOption() {
            const options = [
                { value: 'color', label: 'color' },
                { value: 'size', label: 'size' },
            ];
            return options;
        },
        filterOption() {
            const options = [
                { value: '>=', label: '>=' },
                { value: '<=', label: '<=' },
                { value: '=', label: '=' },
            ];
            const firstItem = globalData.table_data[0];
            if (this.selectedDataOption) {
                if (this.isNumeric(firstItem[this.selectedDataOption])) {
                    return options.slice(0, options.length - 1);
                } else {
                    return options.slice(2, options.length);
                }
            }
        },
        filter2SelectOption() {
            if (this.selectedDataOption) {
                const selectedData = []
                const item = globalData.mappingData[this.assignId];
                for (let i = item.from - 1; i < item.to; i++) {
                    selectedData.push(globalData.table_data[i][item.option]);
                }

                const optionsValue = Array.from(new Set(selectedData));
                let options = [];
                optionsValue.forEach(optionValue => {
                    options.push({ value: optionValue, label: optionValue })
                });
                return options;
            }
            return null;
        },
        handleFilterChange() {
            this.updateData()
        },
        handleFilter2SelectChange() {
            this.updateData()
            console.log(this.filter2Select)
        },
        handleDataChange() {
            if (this.selectedDataOption) {
                this.from = 1;
                this.to = this.dataLength;
                this.selectedVisOption = 'size'

            } else {
                this.selectedFilterOption = null;
                this.from = 0;
                this.to = 0;
                this.selectedVisOption = null;
            }
            this.updateData();
            this.handleVisChange();

        },
        handleFilter1Input() {
            //数字限制
            this.filter1Input = this.filter1Input.replace(/\D/g, '') * 1;
            this.updateData()
        },
        fromInput() {
            //数字限制
            this.from = this.from.replace(/\D/g, '') * 1;
            this.updateData()
        },
        fromInputChange() {
            //12大小限制
            if (this.from > this.to) {
                ElMessage({
                    message: 'wrong number',
                    grouping: true,
                    type: 'warning',
                })
                this.from = '';
                return;

            }
            //范围限制
            if (this.from < 1 || this.from > this.dataLength) {
                this.from = '';
                return;
            }
        },
        toInput() {
            //数字限制
            this.to = this.to.replace(/\D/g, '') * 1;
            this.updateData()

        },
        toInputChange() {
            console.log(this.from, this.to)
            //12大小限制
            if (this.from > this.to) {
                ElMessage({
                    message: 'wrong number',
                    grouping: true,
                    type: 'warning',
                })

                this.to = '';
                return;

            }
            //范围限制
            if (this.to < 1 || this.to > this.dataLength) {
                this.to = '';
                return;
            }
        },
        handleVisChange() {
            //更新selectedVis
            if (this.selectedVisOption) {
                let index = globalData.emitDetail.findIndex(item => item.assignId === this.assignId)
                globalData.emitDetail[index]['selectedVis'] = this.selectedVisOption;
            }
            else {
                let index = globalData.emitDetail.findIndex(item => item.assignId === this.assignId)
                globalData.emitDetail[index]['selectedVis'] = null;
            }

            //更新mappingData
            if (!globalData.mappingData[this.assignId]) {
                // 如果不存在，初始化为一个空对象
                globalData.mappingData[this.assignId] = {};
            }
            if (this.selectedVisOption) {
                globalData.mappingData[this.assignId]['vis'] = this.selectedVisOption;
            }
            else {
                globalData.mappingData[this.assignId]['vis'] = null;
            }
        },
        updateData() {
            //更新mappingData
            let img = globalData.emitDetail.find(item => item.assignId === this.assignId)['img']
            if (!globalData.mappingData[this.assignId]) {
                // 如果不存在，初始化为一个空对象
                globalData.mappingData[this.assignId] = {};
            }
            if (!this.selectedDataOption) {
                this.selectedDataOption = null;
                this.selectedFilterOption = null;
                this.filter1Input = null;
                this.filter2Select = null;
                this.selectedVisOption = null;
            }
            if (!this.selectedFilterOption) {
                this.filter1Input = null;
                this.filter2Select = null;
                this.selectedFilterOption = null;
            }
            globalData.mappingData[this.assignId]['from'] = this.from;
            globalData.mappingData[this.assignId]['to'] = this.to;
            globalData.mappingData[this.assignId]['img'] = img;
            globalData.mappingData[this.assignId]['filterOption'] = this.selectedFilterOption;
            globalData.mappingData[this.assignId]['option'] = this.selectedDataOption;
            globalData.mappingData[this.assignId]['filter1Input'] = this.filter1Input;
            globalData.mappingData[this.assignId]['filter2Select'] = this.filter2Select;

            //更新selectedData
            if (this.selectedDataOption) {
                let index = globalData.emitDetail.findIndex(item => item.assignId === this.assignId)
                //安排选择的数据
                const array = [];
                for (let i = this.from - 1; i < this.to; i++) {
                    array.push(globalData.table_data[i][this.selectedDataOption]);
                }
                globalData.emitDetail[index]['selectedData'] = array;
                if (this.selectedFilterOption && (this.filter1Input || this.filter2Select)) {//如果存在过滤器
                    if (this.filter1Input) {//如果是数字模式
                        let result;
                        if (this.selectedFilterOption === '>=') {
                            result = array
                                .map(num => Number(num))  // 将字符串转换为数字
                                .filter(num => num >= this.filter1Input);  // 过滤数字
                        }
                        else if (this.selectedFilterOption === '<=') {
                            result = array
                                .map(num => Number(num))  // 将字符串转换为数字
                                .filter(num => num <= this.filter1Input);  // 过滤数字
                        }
                        globalData.emitDetail[index]['selectedData'] = result;
                    }
                    else {
                        globalData.emitDetail[index]['selectedData'] = array.filter(element => element === this.filter2Select);
                    }
                }

                //检查是否有线分支筛选，初始化有线筛选
                globalData.lineDetail.forEach((item, i) => {
                    if (item.assignId === this.assignId) {
                        globalData.filteredData[globalData.lineDetail[i].lineId] = {};
                        globalData.lineDetail[i].filteredData = globalData.emitDetail[i]['selectedData'];
                        if(this.filterOption()?.length == 1){
                            globalData.filteredData[globalData.lineDetail[i].lineId]['filter2Select'] = 'ALL';
                        }
                        else if(this.filterOption()?.length >1){
                            globalData.filteredData[globalData.lineDetail[i].lineId]['filter1Select'] = 'ALL';
                        }
                    }
                });
            }
            else {
                const index = globalData.emitDetail.findIndex(item => item.assignId === this.assignId)
                globalData.emitDetail[index]['selectedData'] = [];

                //检查是否有线分支筛选，清空有线筛选
                globalData.lineDetail.forEach((item, i) => {
                    if (item.assignId === this.assignId && item.filteredData && item.filteredData.length > 0) {
                        // 通过索引来确保修改到 globalData.lineDetail
                        globalData.lineDetail[i].filteredData = [];
                        delete globalData.filteredData[globalData.lineDetail[i].lineId];
                    }
                });
            }



        }
    },

}
</script>

<style>
@import '../assets/css/mapping.css';
</style>