import { reactive, watch } from 'vue'
import Mapping from './components/mapping.vue';
const globalData = reactive({
  collaging: false,//是否正在拼贴
  draggingEle: false,//是否正在拖动
  //板块展示
  showTable: false,
  showCollage: false,
  showCanvas: true,
  showEdit: false,
  emitDetail: [],//详细信息{ "type": 'line', "point": [[],[]], 'areaId': 0 }
  table_data: [],//表格数据
  processId: -1,
  canvasHeight: 0,
  canvasWidth: 0,
  mask: '',
  mappingData:{},//每个元素的mapping数据,key为assignId
  filteredData:{},//每个线条的过滤数据，key为lineId
  lineDetail:[],
  okToCollage:false,
  collageResult:null,
  //配置
  gravityEnable:false,
  IP:'localhost'
  // IP:'192.168.31.222'
})
// 监听整个 globalData 的变化
watch(globalData, (newValue, oldValue) => {
  console.log('globalData changed', newValue);
}, { deep: true });
export default globalData