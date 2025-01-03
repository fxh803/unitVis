<script setup>
import canvasComponent from './components/canvas.vue';
import globalData from './globalData';
import tableComponent from './components/table.vue';
import eleCanvasComponent from './components/eleCanvas.vue';
import eleContainerComponent from './components/eleContainer.vue';
import collageComponent from './components/collage.vue';
import EventBus from "@/EventBus";
import { ElMessage, ElMessageBox } from 'element-plus'
</script>
<template>
  <div class="myContainer">
    <div class="header"></div>
    <div class="content">

      <transition name="canvas-slide">
        <div v-show="globalData.showCanvas" class="canvas-component-container">

          <canvas-component></canvas-component>

          <transition name="collage-slide">
            <div v-if="globalData.okToCollage" class="collage-component-container">
              <collage-component></collage-component>
            </div>
          </transition>

        </div>
      </transition>

      <div class="widget-container">

        <transition name="table-slide">
          <div v-if="globalData.showTable" class="table-component-container">
            <table-component></table-component>
          </div>
        </transition>

        <transition name="edit-slide">
          <div v-show="globalData.showEdit" class="edit-container">
            <div class="edit-wrapper">

              <div class="eleContainer-component-container">
                <ele-container></ele-container>
              </div>

              <div class="eleCanvas-component-container">
                <ele-canvas></ele-canvas>
              </div>

            </div>            
          </div>
        </transition>
        <div v-if="globalData.collaging" class="disable-div"></div>
      </div>


    </div>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
    };
  },
  components: {
    'canvas-component': canvasComponent,
    'table-component': tableComponent,
    'ele-container': eleContainerComponent,
    'ele-canvas': eleCanvasComponent,
    'collage-component': collageComponent
  },
  mounted() {
    document.addEventListener('dragend', function (event) {
      globalData.draggingEle = false;
      console.log('Drag operation ended.', globalData);
    });
    this.modalPop();
  },
  methods: {
    modalPop() {
      ElMessageBox.confirm(
        'Welcome to the system, click the button below to start collaging your images',
        ' Welcome',
        {
          showCancelButton: false,
          showClose: false,
          confirmButtonText: "let's start",
          type: 'success',
          center: true,
          closeOnClickModal: false
        }
      )
        .then(() => {
          globalData.showTable = true;
          globalData.showCanvas = true;
          globalData.showEdit = true;
        })

    }
  }
}

</script>

<style>
@import './assets/css/index.css';
</style>