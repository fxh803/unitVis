<script setup>
import { Toast } from "bootstrap";
import paper from "paper";
import { VSwatches } from 'vue3-swatches'
import 'vue3-swatches/dist/style.css'
import { PaperOffset } from "paperjs-offset";
import globalData from '@/globalData';
import EventBus from '@/EventBus';
</script>
<template>
  <div class="eleCanvas-container">
    <canvas class="eleCanvas" id="eleCanvas" @mousedown="handleMouseDown" @mousemove="handleMouseMove"
      @mouseup="handleMouseUp" @mouseleave="handleMouseLeave" draggable="false">
    </canvas>
    <div v-if="imgUrl !== ''" class="img-container" draggable="false">
      <img class="drawImg" draggable="true" @dragstart="onDrawImgDragstart" :src="imgUrl" />
    </div>
    <div class="btn-container" >
      <v-swatches v-model="color" class="color-picker"
        :trigger-style="{ width: '30px', height: '30px', 'border-radius': '50%' }"
        :swatch-style="{ 'border-radius': '50%' }" show-fallback fallback-input-type="color"
        popover-x="left" popover-y="bottom"></v-swatches>
      <button type="button" class="btn btn-primary editBtn" :style="{ opacity: btnOpacity['write-btn'] }"
        @click="writeCanvas">
        <i class="bi bi-pencil-square"></i>
      </button>
      <button type="button" class="btn btn-danger editBtn" :style="{ opacity: btnOpacity['clean-btn'] }"
        @click="clearCanvas">
        <i class="bi bi-trash3-fill"></i>
      </button>
    </div>

  </div>
  <div class="toast-container position-fixed" id="toast-container2">
    <div id="liveToast2" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="toast-header">
        <strong>closed this stoke?</strong>
      </div>
      <div class="toast-body">
        <button type="button" class="btn btn-primary" @click="closePath">
          yes
        </button>
        <button type="button" class="btn btn-danger" @click="hideToast">
          no
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "eleCanvasComponent",
  components: {
    'v-swatches': VSwatches
  },
  data() {
    return {
      color: '#1CA085',
      isDrawing: false,
      mode: 0, // 0: Not drawing, 1: Drawing mode
      nowX: 0,
      nowY: 0,
      canvas: null,
      btnOpacity: {
        "write-btn": 1,
        "clean-btn": 1,
      },
      paths: [],
      path: null,
      toast: null,
      step: -1,
      imgUrl: ''
    };
  },
  mounted() {
    const canvas = document.getElementById("eleCanvas");
    this.canvas = canvas;
  },

  methods: {
    onDrawImgDragstart(event) {
      paper.projects[0].activate();
      const imageUrl = event.target.src;
      event.dataTransfer.setData('text/plain', imageUrl);
      globalData.draggingEle= true;
      const x = event.clientX;
      const y = event.clientY; 
      event.dataTransfer.setData('text/positionX', JSON.stringify(x));
      event.dataTransfer.setData('text/positionY', JSON.stringify(y));
    },
    handleMouseDown(e) {
      if (this.mode == 1) {
        paper.projects[paper.projects.length-1].activate();//保证激活
        this.isDrawing = true;
        this.hideToast()
        var rect = this.canvas.getBoundingClientRect();
        [this.nowX, this.nowY] = [e.clientX - rect.left, e.clientY - rect.top];
        let newPath = new paper.Path({
          strokeColor: this.color,
          strokeWidth: 7,
        });
        newPath.moveTo(new paper.Point(this.nowX, this.nowY));

        newPath.bringToFront();
        this.path = newPath;
        this.paths.push(newPath);
      }
    },
    handleMouseMove(e) {
      if (this.mode == 1) {
        if (this.isDrawing) {
          var rect = this.canvas.getBoundingClientRect();
          [this.nowX, this.nowY] = [
            e.clientX - rect.left,
            e.clientY - rect.top,
          ];
          this.path.add(new paper.Point(this.nowX, this.nowY));
        }
      }
    },
    handleMouseLeave(e) {
      this.isDrawing = false;
    },
    handleMouseUp(e) {
      if (this.mode == 1) {
        this.isDrawing = false;
        //如果画的太短
        if (this.path.segments.length > 10) {
          this.path.simplify(10);
          const liveToast = document.getElementById("liveToast2");
          liveToast.addEventListener('hidden.bs.toast', () => {
            setTimeout(function() {
            this.imgUrl = this.canvas.toDataURL('image/png');
            }.bind(this), 100);
          })
          const toastContainer = document.getElementById("toast-container2");
          const windowWidth = window.innerWidth;
          const windowHeight = window.innerHeight;
          // 计算 toastContainer 的位置
          let leftPos = e.clientX;
          let topPos = e.clientY;

          // 获取元素的计算样式
          const computedStyle = window.getComputedStyle(liveToast);
          // 获取计算样式中的宽度和高度
          const toastWidth = parseInt(computedStyle.getPropertyValue("width"), 10);
          const toastHeight = parseInt(computedStyle.getPropertyValue("height"), 10);
          // 检查是否超出右边界
          if (leftPos + toastWidth > windowWidth) {
            leftPos = windowWidth - toastWidth;
          }
          // 检查是否超出底部边界
          if (topPos + toastHeight > windowHeight) {
            topPos = windowHeight - toastHeight;
          }
          // 设置 toastContainer 的位置
          toastContainer.style.left = Math.max(0, leftPos) + "px";
          toastContainer.style.top = Math.max(0, topPos) + "px";
          this.toast = new Toast(liveToast);
          this.toast.show();
        } else {
          this.path.remove();
        }

      }
    },
    writeCanvas() {
      if (this.mode == 0) {
        this.mode = 1;
        paper.setup(this.canvas);
      } else {
        this.mode = 0;
      }
    },
    clearCanvas() {
      if (this.paths != []) {
        this.paths.forEach((path) => {
          path.remove();
        });
        this.imgUrl=''
      }
      if (this.toast != null)
        this.toast.hide();
    },
    uploadCanvas() {
      this.mode = 0;
      this.clearCanvas();
    },
    hideToast() {
      if (this.toast != null)
        this.toast.hide();
      this.path = null;
    },
    closePath() {
      this.path.closed = true;
      // 填充路径
      this.path.fillColor = this.color;
      this.toast.hide();
      this.path = null;
      // console.log(this.path);
    },
  },
  watch: {
    mode: {
      handler(newValue, oldValue) {
        if (newValue == 0) {
          this.btnOpacity['write-btn'] = 1;
        }
        else if (newValue == 1) {
          this.btnOpacity['write-btn'] = 0.3;
        }
      },

    },
  }
}
</script>

<style>
@import "../assets/css/eleCanvas.css";
</style>
