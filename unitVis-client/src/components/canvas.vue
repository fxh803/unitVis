<script setup>
import { Toast } from "bootstrap";
import paper from "paper";
import { PaperOffset } from "paperjs-offset";
import globalData from "@/globalData";
import EventBus from "@/EventBus";
import mappingComponent from "./mapping.vue";
import filterComponent from "./filter.vue";
import animationComponent from "./animation.vue";
import { ElMessage } from 'element-plus';
import { gsap } from "gsap";
</script>
<template>
  <div class="canvas-container">
    <canvas class="canvas" id="canvas" @mousedown="handleMouseDown" @mousemove="handleMouseMove"
      @mouseup="handleMouseUp" @dragover="handleDragOver" @drop="handleDrop" @mouseleave="handleMouseLeave">
    </canvas>

    <div v-if="!globalData.collaging" class="btn-container">
      <button id="write-btn" type="button" class="btn btn-primary editBtn" :style="{ opacity: btnOpacity['write-btn'] }"
        @click="writeCanvas">
        <i class="bi bi-pencil-square"></i>
      </button>
      <button id="clean-btn" type="button" class="btn btn-danger editBtn" :style="{ opacity: btnOpacity['clean-btn'] }"
        @click="clearCanvas">
        <i class="bi bi-trash3-fill"></i>
      </button>

      <el-dropdown trigger="click">
        <button id="upload-btn" type="button" class="btn btn-success editBtn"
          :style="{ opacity: btnOpacity['upload-btn'] }">
          <input type="file" class="fileInput" id="maskInput" accept=".jpg , .png" @change="uploadMaskChange">
          <input type="file" class="fileInput" id="backgroundInput" accept=".jpg , .png"
            @change="uploadBackgroundChange">
          <i class="bi bi-upload"></i>
        </button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="uploadMaskClick">upload mask</el-dropdown-item>
            <el-dropdown-item @click="uploadBackgroundClick">upload background</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

    </div>
    <!-- 每个元素的删除按钮 -->
    <el-button v-if="!globalData.draggingEle && !globalData.collaging" v-for="(message, index) in delMessage"
      :key="message.assignId" class="delBtn" :id="'delBtn' + message.assignId"
      :style="{ position: 'absolute', left: message.x + 'px', top: message.y + 'px' }" type="danger" icon="Close"
      @click="deleteEmit(message.assignId)">
    </el-button>
  </div>

  <div class="toast-container strokeToast-container position-fixed">
    <div id="strokeToast" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="toast-header">
        <strong>closed this stoke?</strong>
      </div>
      <div class="toast-body">
        <button type="button" class="btn btn-primary strokeBtn" @click="closePath">
          yes
        </button>
        <button type="button" class="btn btn-danger strokeBtn" @click="dontClosePath">
          no
        </button>
      </div>
    </div>
  </div>

  <div v-if="globalData.table_data.length > 0" class="toast-container mappingToast-container position-fixed">
    <div id="mappingToast" class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-bs-autohide="false">
      <div class="toast-body">
        <mapping-component v-if="mappingToast != null" :assignId="mappingEleId"></mapping-component>
      </div>
    </div>
  </div>

  <div class="toast-container lineToast-container position-fixed">
    <div id="lineToast" class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-bs-autohide="false">
      <div class="toast-body">
        <filter-component v-if="lineToast != null" :lineId="selectedLineLineId"></filter-component>
        <button type="button" class="btn btn-danger deleteLineBtn"
          @click="removeLine(selectedLineLineId, selectedLineAssignId)">
          remove this trace
        </button>

      </div>
    </div>
  </div>

  <div class="toast-container maskToast-container position-fixed">
    <div id="maskToast" class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-bs-autohide="false">
      <div class="toast-body">
        <button type="button" class="btn btn-danger deleteMaskBtn" @click="removeMask()">
          remove this mask
        </button>

      </div>
    </div>
  </div>

  <animation-component v-show="!globalData.draggingEle"></animation-component>

  <img class="animated-image" id="animated-image"  v-show="animatedImage" :src="animatedImage" alt="Image" />

</template>

<script>
export default {
  name: "canvasComponent",
  components: {
    'mapping-component': mappingComponent,
    'filter-component': filterComponent,
    'animation-component': animationComponent
  },
  computed: {
    globalData() {
      return globalData;
    },
    collaging() {
      return globalData.collaging;
    }

  },
  data() {
    return {
      delMessage: [],
      isDrawing: false,
      mode: 0,
      nowX: 0,
      nowY: 0,
      canvas: null,
      btnOpacity: {
        "write-btn": 1,
        "clean-btn": 1,
        "upload-btn": 1,
      },
      paths: [],//保存绘制的所有路径
      backgroundRaster: null,
      emitLines: [],//保存线型发射区域
      emitPoints: [],//保存点型发射区域
      emitMasks: [],//保存掩膜发射区域
      path: null,//当前绘制的对象
      strokeToast: null,
      mappingToast: null,
      lineToast: null,
      maskToast: null,
      draggingPath: false,
      lastHoverObj: null,

      emitAreaSigns: [],//保存发射记号
      assignCounter: 0,
      lineCounter: 0,
      line_Path: null,
      line_Paths: [],
      safe_place_release: false,
      controlPoints: {},
      mappingEleId: null,//点击mapping的assignid
      areaCounter: 0,
      selectedLineLineId: null,//点击filter的lineId
      selectedLineAssignId: null,
      selectedMaskAreaId: null,//点击mask的areaId
      areaPoints: [],//后台返回的轮廓点
      blackThingOpacity: 0.5,
      animatedImage: null
    };
  },
  mounted() {
    const canvas = document.getElementById("canvas");
    this.canvas = canvas;
    paper.setup(canvas);
    globalData.canvasHeight = canvas.offsetHeight;
    globalData.canvasWidth = canvas.offsetWidth;

    // 绑定全局点击事件
    document.addEventListener('mousedown', this.mousedownListener);
    // 绑定全局点击事件
    document.addEventListener('dragend', this.dragendListener);

    EventBus.on('prepareCollage', this.prepareCollage);

  },
  methods: {

    mousedownListener(event) {
      // 获取鼠标在canvas中的位置
      const rect = canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      var hitResult = paper.project.activeLayer.hitTest(new paper.Point(x, y));
      const isInsideToast = event.target.closest('.toast');
      const isInsideElSelect = String(event.target.className).includes('el-select') || String(event.target.parentNode.className).includes('el-select')

      if (!hitResult?.item.isEmitSigns && !isInsideToast && !isInsideElSelect) {
        this.hideMappingToast();
        this.mappingToast = null;
      }

      const toastElement1 = document.getElementById('strokeToast'); // 获取你的 toast 元素
      if (toastElement1?.classList.contains('show') && !isInsideToast) {
        this.hideStrokeToast();
        this.dontClosePath();
      }

      const toastElement2 = document.getElementById('lineToast'); // 获取你的 toast 元素
      if (toastElement2?.classList.contains('show') && !isInsideToast && !isInsideElSelect) {
        this.hideLineToast();
        this.lineToast = null;
        this.selectedLineAssignId = null;
        this.selectedLineLineId = null;
      }

      const toastElement3 = document.getElementById('maskToast'); // 获取你的 toast 元素
      if (toastElement3?.classList.contains('show') && !isInsideToast) {
        this.hideMaskToast();
        this.maskToast = null;
      }
    },
    dragendListener(event) {
      //解决拖动元素不正确释放
      if (globalData.draggingEle) {
        //重新显示
        this.showCanvasForeground();
        this.showLineTrack();
      }
    },
    updateAnimation() {
      // 在每帧更新所有动画
      paper.view.onFrame = (event) => {
        for (let i = 0; i < this.emitPoints.length; i++) {
          let area = this.emitPoints[i];
          area.opacity += area.changeRate;
          if (area.opacity > 1) {
            area.changeRate = -0.01;
          }
          if (area.opacity < 0) {
            area.changeRate = 0.01;
          }
        }

        if (this.line_Paths) {
          // 遍历所有路径，更新虚线的动画
          for (let i = 0; i < this.line_Paths.length; i++) {
            let path = this.line_Paths[i];
            // 移动虚线的起始位置
            path.dashOffset -= 0.2; // 增加偏移量
            // 如果偏移量超过某个值，则重置
            if (path.dashOffset > 15) {
              path.dashOffset = 0; // 重置偏移量
            }
          }
        }

      };
    },
    //图标拖动函数
    handleDragOver(e) {
      e.preventDefault();
      if (globalData.draggingEle) {
        //隐藏前景
        this.hideCanvasForeground();
        this.hideLineTrack();
        // 获取鼠标在canvas中的位置
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        // 使用Paper.js的hitTest方法检测鼠标是否悬停在对象上
        var hitResult = paper.project.activeLayer.hitTest(new paper.Point(x, y));
        //前一个隐藏
        if (this.lastHoverObj != null) {
          if (this.lastHoverObj.emitType !== 'area' && this.lastHoverObj.emitType !== 'mask')
            this.lastHoverObj.opacity = 0;
          else {
            if (this.lastHoverObj.fillColor)
              this.lastHoverObj.fillColor = 'black';
            this.lastHoverObj.strokeColor = 'black';
          }
          this.lastHoverObj = null;
        }
        if (hitResult && hitResult.item.isEmitArea) {
          this.lastHoverObj = hitResult.item;
          if (this.lastHoverObj.emitType !== 'area' && this.lastHoverObj.emitType !== 'mask')
            this.lastHoverObj.opacity = 1;
          else {
            if (this.lastHoverObj.fillColor)
              this.lastHoverObj.fillColor = new paper.Color(0, 95 / 255, 204 / 255);

            this.lastHoverObj.strokeColor = new paper.Color(0, 95 / 255, 204 / 255);
          }
        }
      }

    },
    //图标放下函数
    handleDrop(e) {
      e.preventDefault();
      if (globalData.draggingEle) {

        //重新显示
        this.showCanvasForeground();
        this.showLineTrack();
        const imageUrl = e.dataTransfer.getData("text/plain");
        const initPosX = JSON.parse(e.dataTransfer.getData('text/positionX'));
        const initPosY = JSON.parse(e.dataTransfer.getData('text/positionY'));
        console.log(initPosX, initPosY);
        this.animatedImage = imageUrl;
        var rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // 使用 GSAP 实现动画
        const animatedElement = document.getElementById('animated-image');
        animatedElement.style.left = initPosX - rect.left + 'px';
        animatedElement.style.top = initPosY - rect.top + 'px';
        gsap.to(animatedElement, {
          y: e.clientY - initPosY,
          ease: "bounce.out", // 弹跳效果
          duration: 1,
          opacity: 1,
          onComplete:   () => {
            // 元素移动完成后的操作
            gsap.to(animatedElement, {
              y: 0,  
              duration: 0,  
            });
            this.animatedImage = null;
          }
        });
        gsap.to(animatedElement, {
          x: e.clientX - initPosX,
          ease: "poower2.out", // 弹跳效果
          duration: 1,
          opacity: 1,
          onComplete:   () => {
            // 元素移动完成后的操作
            gsap.to(animatedElement, {
              x: 0, 
              duration: 0,  
            });
            this.animatedImage = null;
          }
        });
        // 创建发射标记
        // 创建一个 Raster 对象并加载图片
        var raster = new paper.Raster({
          source: imageUrl,                // 使用 `source` 来指定图片的 URL
          position: new paper.Point(x, y),
          opacity: 0,
          isEmitSigns: true
        });
        raster.assignId = this.assignCounter;
        // 当图片加载完成后
        raster.onLoad = () => {
          raster.opacity = 1;
          // 获取原始图片的宽高
          var originalWidth = raster.width;
          var originalHeight = raster.height;
          // 计算保持宽高比的缩放比例
          var scaleX = 40 / originalWidth;
          var scaleY = 40 / originalHeight;

          // 使用较小的缩放比例来保证不会拉伸图片
          var scaleFactor = Math.min(scaleX, scaleY);

          // 按比例缩放图片
          raster.scale(scaleFactor);

          var finalWidth = raster.width * scaleFactor;
          var finalHeight = raster.height * scaleFactor;
          //添加删除信息
          this.delMessage.push({
            x: x + finalWidth / 2 - 5,
            y: y - finalHeight / 2 + 5,
            assignId: raster.assignId,
            assignUrl: imageUrl
          })

          //如果是放在线和面上
          if (this.lastHoverObj != null) {
            this.lastHoverObj.assignId.push(this.assignCounter);
            if (this.lastHoverObj.emitType == 'line') {
              // 访问路径的点数组
              var pointsArray = [];
              for (var i = 0; i < this.lastHoverObj.segments.length; i++) {
                pointsArray.push([this.lastHoverObj.segments[i].point.x, this.lastHoverObj.segments[i].point.y]);
              }
              globalData.emitDetail.push({ "img": imageUrl, "type": 'line', "assignPoint": [x, y], "areaPoints": pointsArray, 'areaId': this.lastHoverObj.areaId, 'assignId': this.assignCounter, 'renderWidth': finalWidth, 'renderHeight': finalHeight })
            }

            else if (this.lastHoverObj.emitType == 'area') {
              var pointsArray = [];
              this.areaPoints.forEach(points => {
                if (this.isPointInsidePolygon([x, y], points)) {
                  pointsArray = points;
                }
              });
              globalData.emitDetail.push({ "img": imageUrl, "type": 'area', "assignPoint": [x, y], "areaPoints": pointsArray, 'areaId': this.lastHoverObj.areaId, 'assignId': this.assignCounter, 'renderWidth': finalWidth, 'renderHeight': finalHeight })
            }
            else if (this.lastHoverObj.emitType == 'mask') {
              // 访问路径的点数组
              var pointsArray = [];
              for (var i = 0; i < this.lastHoverObj.segments.length; i++) {
                pointsArray.push([this.lastHoverObj.segments[i].point.x, this.lastHoverObj.segments[i].point.y]);
              }

              globalData.emitDetail.push({ "img": imageUrl, "type": 'area', "assignPoint": [x, y], "areaPoints": pointsArray, 'areaId': this.lastHoverObj.areaId, 'assignId': this.assignCounter, 'renderWidth': finalWidth, 'renderHeight': finalHeight })
            }
            this.lastHoverObj = null;
          }
          else {
            globalData.emitDetail.push({ "img": imageUrl, "type": 'point', "assignPoint": [x, y], 'assignId': this.assignCounter, 'renderWidth': finalWidth, 'renderHeight': finalHeight })
          }
          this.emitAreaSigns.push(raster)
          this.assignCounter += 1;

        };
        //元素点下之后
        raster.onMouseDown = (e) => {
          //检查assign类型是不是点类型
          if (globalData.emitDetail.find(item => item.assignId === raster.assignId)['type'] == 'point') {
            this.mode = 2;
            this.isDrawing = true;
            let newPath = new paper.Path({
              strokeColor: '#FFC107',
              opacity: 0.7,
              strokeWidth: 5,
              dashArray: [10, 4],
              assignId: raster.assignId,
              lineId: this.lineCounter
            });

            this.lineCounter += 1;
            //点击轨迹事件
            newPath.onMouseUp = (e) => {
              //一大段计算toast
              this.selectedLineAssignId = newPath.assignId;
              this.selectedLineLineId = newPath.lineId;
              const toast = document.getElementById("lineToast");
              const toastContainer = document.querySelector(".lineToast-container");
              // 计算 toastContainer 的位置
              const viewPosition = paper.project.view.viewToProject(e.point);
              const { x, y } = viewPosition;
              let leftPos = x;
              let topPos = y;
              // 设置 toastContainer 的位置
              toastContainer.style.left = Math.max(0, leftPos) + "px";
              toastContainer.style.top = Math.max(0, topPos) + "px";
              this.lineToast = new Toast(toast);
              if (this.lineToast) {
                this.showLineToast();
              }
            }

            newPath.bringToFront();
            this.line_Path = newPath;
            this.line_Paths.push(newPath);
            this.updateAnimation();
          }


        };
        raster.onMouseUp = (e) => {
          this.mode = 0;
          this.isDrawing = false;
          if (globalData.table_data.length > 0) {
            if (this.mappingToast) {
              this.hideMappingToast();
              this.mappingToast = null;
              this.mappingEleId = null;
            }
            else {
              //一大段计算toast
              const toast = document.getElementById("mappingToast");
              const toastContainer = document.querySelector(".mappingToast-container");
              let posX = raster.position.x;
              let posY = raster.position.y;
              // 计算 toastContainer 的位置
              let leftPos = posX + 5;
              let topPos = posY + 5;
              // 设置 toastContainer 的位置
              toastContainer.style.left = Math.max(0, leftPos) + "px";
              toastContainer.style.top = Math.max(0, topPos) + "px";
              this.mappingToast = new Toast(toast);
              if (this.mappingToast) {
                this.showMappingToast();
                this.mappingEleId = raster.assignId;
              }
            }
          }
          else {
            ElMessage({
              message: " please upload dataset first !",
              grouping: true,
              type: 'warning',
            })
          }


        }

      }
    },
    //点击开始绘画
    handleMouseDown(e) {
      console.log(this.mode, this.draggingPath, this.path)
      if (this.mode == 1 && !this.draggingPath && !this.path) {
        var rect = this.canvas.getBoundingClientRect();
        var hitResult = paper.project.activeLayer.hitTest(new paper.Point(e.clientX - rect.left, e.clientY - rect.top));
        //如果在已有area和sign上绘制，是不行的
        if (hitResult && (hitResult?.item.isEmitArea || hitResult?.item.isEmitSigns)) {
          return;
        }
        console.log('drawing')
        this.isDrawing = true;
        let newPath = new paper.Path({
          strokeColor: 'black',
          strokeWidth: 10,
          assignId: [],
          areaId: this.areaCounter,
          isEmitArea: true,
          finishDrawing: false,
          emitType: 'area'
        });
        this.areaCounter += 1;
        newPath.moveTo(new paper.Point(e.clientX - rect.left, e.clientY - rect.top));


        newPath.onMouseEnter = (event) => {
          if (newPath.finishDrawing) {

            if (newPath.assignId.length == 0 && !globalData.collaging) {
              if (newPath.fillColor)
                newPath.fillColor = new paper.Color(0, 95 / 255, 204 / 255);
              newPath.strokeColor = new paper.Color(0, 95 / 255, 204 / 255);
            }
            if (this.mode == 2 && this.isDrawing) {
              this.line_Path.strokeColor = '#4CAF50';
              this.safe_place_release = true;
              this.line_Path.areaId = newPath.areaId;
            }

          }
        };

        newPath.onMouseLeave = (event) => {
          if (newPath.finishDrawing) {
            if (newPath.assignId.length == 0 && !globalData.collaging) {
              if (newPath.fillColor)
                newPath.fillColor = 'black';
              newPath.strokeColor = 'black';
            }
            if (this.mode == 2 && this.isDrawing) {
              this.line_Path.strokeColor = '#FFC107';
              this.safe_place_release = false;
              this.line_Path.areaId = null;
            }
            if (!newPath.closed)
              this.draggingPath = false;
          }

        };
        newPath.onMouseDrag = (event) => {
          if (!newPath.closed && newPath.finishDrawing) {
            this.draggingPath = true;
            let deltaX = event.delta.x;
            let deltaY = event.delta.y;
            let currentWidth = newPath.strokeWidth;
            let newWidth = currentWidth + (deltaX + deltaY) / 5;
            newPath.strokeWidth = Math.max(1, newWidth);
          }
        };

        newPath.onMouseUp = (event) => {
          if (newPath.finishDrawing) {
            if (this.draggingPath) {
              this.draggingPath = false;
              //重新生成拉伸path的line
              this.emitLines = this.emitLines.filter((line) => {
                line.remove();
                return false; // 不保留该项
              });
              this.exportCanvas();
            }
            else {
              if (this.maskToast) {
                this.hideMaskToast();
                this.maskToast = null;
              } else {
                //一大段计算toast
                this.selectedMaskAreaId = newPath.areaId;
                const toast = document.getElementById("maskToast");
                const toastContainer = document.querySelector(".maskToast-container");
                // 计算 toastContainer 的位置
                const viewPosition = paper.project.view.viewToProject(event.point);
                const { x, y } = viewPosition;
                this.nowX = x;
                this.nowY = y;
                let leftPos = x;
                let topPos = y;
                // 设置 toastContainer 的位置
                toastContainer.style.left = Math.max(0, leftPos) + "px";
                toastContainer.style.top = Math.max(0, topPos) + "px";
                this.maskToast = new Toast(toast);
                if (this.maskToast) {
                  this.showMaskToast();
                }
              }
            }
          }
        };
        newPath.bringToFront();
        this.path = newPath;
        this.paths.push(newPath);
      }

    },
    //移动绘画
    handleMouseMove(e) {
      if (this.isDrawing) {
        if (this.mode == 1 && !this.draggingPath) {

          var rect = this.canvas.getBoundingClientRect();

          this.path.add(new paper.Point(e.clientX - rect.left, e.clientY - rect.top));

        }
        else if (this.mode == 2) {
          var rect = this.canvas.getBoundingClientRect();
          this.line_Path.add(new paper.Point(e.clientX - rect.left, e.clientY - rect.top));
        }
      }
    },
    //超出画布停止绘画
    handleMouseLeave(e) {
      if (this.mode == 2 && this.isDrawing) {
        this.line_Path.remove();
        this.line_Path = null;
      }
      else if (this.mode == 1 && this.isDrawing) {
        this.path.remove();
        this.path = null;
      }
      this.isDrawing = false;
    },
    //停止绘画
    handleMouseUp(e) {
      if (this.mode == 1 && this.isDrawing) {
        //如果正在拖动，跳出
        if (this.draggingPath) {
          return;
        }
        //如果画的太短
        if (this.path.segments.length > 10) {
          this.isDrawing = false;
          this.path.simplify(50);
          console.log('draw done')
          //一大段计算toast
          const toast = document.getElementById("strokeToast");
          const toastContainer = document.querySelector(".strokeToast-container");
          const windowWidth = window.innerWidth;
          const windowHeight = window.innerHeight;
          // 计算 toastContainer 的位置
          let leftPos = e.clientX + 5;
          let topPos = e.clientY + 5;

          // 获取元素的计算样式
          const computedStyle = window.getComputedStyle(toast);
          // 获取计算样式中的宽度和高度
          const toastWidth = parseInt(
            computedStyle.getPropertyValue("width"),
            10
          );
          const toastHeight = parseInt(
            computedStyle.getPropertyValue("height"),
            10
          );
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
          this.strokeToast = new Toast(toast);
          this.showStrokeToast();

        }
        else {
          this.path.remove();
          this.isDrawing = false;
        }
      }
      else if (this.mode == 2 && this.isDrawing) {
        if (this.safe_place_release) {
          this.safe_place_release = false;
          this.isDrawing = false;
          this.mode = 0;
          this.line_Path.simplify(50);
          this.line_Path.fullySelected = true;
          globalData.lineDetail.push({ 'assignId': this.line_Path.assignId, 'lineId': this.line_Path.lineId, 'areaId': this.line_Path.areaId })

          var pointsArray = this.rebuildPathWithUniformPoints(this.line_Path, Math.floor(this.line_Path.length / 30));
          // 查找 assignId 匹配 this.line_Path.assignId 的项
          let foundItem = globalData.lineDetail.find(item => item.lineId === this.line_Path.lineId);
          if (foundItem) {
            // 初始化 trace 和 traceLastPoint，如果它们不存在
            foundItem['trace'] = foundItem['trace'] || null;
            foundItem['traceLastPoint'] = foundItem['traceLastPoint'] || null;
            // 为找到的项添加新属性
            foundItem['trace'] = pointsArray;
            foundItem['traceLastPoint'] = pointsArray[pointsArray.length - 1];
          }
          // 创建一个圆形路径
          let newPath = new paper.Path.Circle({
            center: new paper.Point(pointsArray[pointsArray.length - 1][0], pointsArray[pointsArray.length - 1][1]), // 设置圆心
            radius: 30, // 设置半径
            strokeColor: 'rgba(0, 119, 255, 0.7)', // 设置边框颜色
            fillColor: 'rgba(0, 119, 255, 0.7)', // 设置填充颜色
            strokeWidth: 0, // 设置边框宽度
            opacity: 0.1, // 设置透明度
            changeRate: 0.03,
            assignId: this.line_Path.assignId,
            lineId: this.line_Path.lineId,
            emitType: 'point', // 自定义属性
          });
          this.emitPoints.push(newPath);
          this.updateAnimation();
          // 添加控制点
          this.line_Path.segments.forEach((segment) => {
            // 获取 handleIn 和 handleOut 的位置相对于 segment.point
            var handleInPos = segment.point.add(segment.handleIn);
            var handleOutPos = segment.point.add(segment.handleOut);

            // 创建可见的 handleIn 和 handleOut 控制点（使用小圆表示）
            var handleInCircle = new paper.Path.Circle({
              center: handleInPos,
              radius: 5,
              fillColor: 'red',
              lineId: this.line_Path.lineId
            });

            var handleOutCircle = new paper.Path.Circle({
              center: handleOutPos,
              radius: 5,
              fillColor: 'blue',
              lineId: this.line_Path.lineId
            });

            if (!this.controlPoints[this.line_Path.lineId]) {
              this.controlPoints[this.line_Path.lineId] = [];  // 初始化为空数组
            }
            // 然后推入控制点
            this.controlPoints[this.line_Path.lineId].push([handleInCircle, handleOutCircle]);

            handleInCircle.onMouseEnter = (event) => {
              this.mode = 0;
            };
            handleOutCircle.onMouseEnter = (event) => {
              this.mode = 0;
            };

            // 使 handleInCircle 可拖动
            handleInCircle.onMouseDrag = (event) => {
              // 更新 handleIn 的位置相对于 segment.point
              segment.handleIn = event.point.subtract(segment.point);
              handleInCircle.position = event.point; // 更新可见控制点的位置
            };

            // 使 handleOutCircle 可拖动
            handleOutCircle.onMouseDrag = (event) => {
              // 更新 handleOut 的位置相对于 segment.point
              segment.handleOut = event.point.subtract(segment.point);
              handleOutCircle.position = event.point; // 更新可见控制点的位置
            };

            // 处理拖动结束的事件
            handleOutCircle.onMouseUp = (event) => {
              this.traceUpdate(handleOutCircle.lineId);
            };
            // 处理拖动结束的事件
            handleInCircle.onMouseUp = (event) => {
              this.traceUpdate(handleInCircle.lineId);
            };
          });
        }
        else {
          this.line_Path.remove();
          this.isDrawing = false;
        }


      }
    },
    //删除轨迹
    removeLine(lineId, assignId) {
      for (let i = this.line_Paths.length - 1; i >= 0; i--) {
        if (this.line_Paths[i].lineId === lineId) {
          // 删除线
          this.removeControlPoints(lineId);
          this.removePointArea(lineId);
          this.line_Paths[i].remove();
          this.line_Paths.splice(i, 1);
        }
      }
      //删除lineDetail对应项
      for (let i = 0; i < globalData.lineDetail.length; i++) {
        if (globalData.lineDetail[i]['lineId'] === lineId) {
          globalData.lineDetail.splice(i, 1);
        }
      }
      //删除filterData对应项
      delete globalData.filteredData[lineId];

      this.hideLineToast();
      this.lineToast = null;
      this.selectedLineAssignId = null;
      this.selectedLineLineId = null;
    },
    //更新轨迹点
    traceUpdate(lineId) {
      const foundLinePath = this.line_Paths.find(path => path.lineId === lineId);
      var pointsArray = this.rebuildPathWithUniformPoints(foundLinePath, Math.floor(foundLinePath.length / 30));

      let foundItem = globalData.lineDetail.find(item => item.lineId === lineId);
      if (foundItem) {
        // 初始化 trace 和 traceLastPoint，如果它们不存在
        foundItem['trace'] = foundItem['trace'] || null;
        foundItem['traceLastPoint'] = foundItem['traceLastPoint'] || null;
        // 为找到的项添加新属性
        foundItem['trace'] = pointsArray;
        foundItem['traceLastPoint'] = pointsArray[pointsArray.length - 1];
      }
    },
    //清除对应轨迹的控制点
    removeControlPoints(lineId) {

      const pointsArray = this.controlPoints[lineId];
      if (pointsArray) {
        pointsArray.forEach(element => {
          element[0].remove();
          element[1].remove();
        });
      }

    },
    //清除对应轨迹的终点蓝圈
    removePointArea(lineId) {
      this.emitPoints = this.emitPoints.filter(area => {
        if (area.lineId === lineId) {
          area.remove(); // 移除图形
          return false;
        }
        return true;
      });
    },
    //删除对应的mask
    removeMask() {
      this.paths = this.paths.filter(path => {
        if (path.areaId === this.selectedMaskAreaId) {
          path.remove();
          return false;
        }
        return true;
      });
      this.emitMasks = this.emitMasks.filter(mask => {
        if (mask.areaId === this.selectedMaskAreaId) {
          mask.remove();
          return false;
        }
        return true;
      });
      //隐藏toast
      this.hideMaskToast();
      this.maskToast = null;

      //检查现有的元素，有没有assign到对应mask上的
      globalData.emitDetail.forEach(detail => {
        if (detail.areaId === this.selectedMaskAreaId) {
          this.deleteEmit(detail.assignId);
        }

      });
      //检查有没有线搭在上面的
      //删除控制点,以及linedetail对应项
      globalData.lineDetail = globalData.lineDetail.filter(line => {
        if (line.areaId === this.selectedMaskAreaId) {
          this.removeControlPoints(line.lineId);
          this.removePointArea(line.lineId);
          return false;
        }
        return true;
      });
      //处理可能轨迹
      for (let i = this.line_Paths.length - 1; i >= 0; i--) {
        if (this.line_Paths[i].areaId === this.selectedMaskAreaId) {
          this.line_Paths[i].remove();
          this.line_Paths.splice(i, 1);  // 删除满足条件的元素
        }
      }
      //处理emitline线上元素
      console.log(this.emitLines)
      const dyingEmitLinesAreaId = []
      for (var i = 0; i < this.areaPoints.length; i++) {
        if (this.isPointInsidePolygon([this.nowX, this.nowY], this.areaPoints[i])) {
          this.emitLines.forEach(line => {
            if (line.boundaryIndex === i) {
              console.log(line.boundaryIndex)
              dyingEmitLinesAreaId.push(line.areaId)
            }
          });
        }
      }
      console.log(dyingEmitLinesAreaId)
      //删除在dyingline上的element
      globalData.emitDetail.forEach(detail => {
        console.log(detail.areaId)
        if (dyingEmitLinesAreaId.includes(detail.areaId)) {
          console.log('删除', detail.areaId)
          this.deleteEmit(detail.assignId);
        }

      });
      // emitline删除
      this.emitLines = this.emitLines.filter((line) => {
        if (dyingEmitLinesAreaId.includes(line.areaId)) {
          line.remove();
          return false;
        }
        return true;
      });

    },
    //准备绘画按钮触发函数
    writeCanvas() {
      if (this.mode != 1) {
        paper.projects[0].activate();
        this.mode = 1;
      } else {
        this.mode = 0;
      }
    },
    //清除画布函数
    clearCanvas() {

      this.paths.forEach((path) => {
        path.remove();
      });
      this.paths = []
      this.emitPoints.forEach((point) => {
        point.remove();
      })
      this.emitPoints = []
      this.emitLines.forEach((line) => {
        line.remove();
      })
      this.emitLines = []
      this.hideStrokeToast();

      this.emitMasks.forEach(mask => {
        mask.remove();
      });
      this.emitMasks = [];
      //删除backgroundRaster
      if (this.backgroundRaster) {
        this.backgroundRaster.remove();
        this.backgroundRaster = null;
      }
      //删除所有元素
      const assignIdList = []
      globalData.emitDetail.forEach(detail => {
        assignIdList.push(detail.assignId)
      });
      assignIdList.forEach(assignId => {
        this.deleteEmit(assignId)
      });

    },
    //上传函数
    uploadMaskClick() {
      this.mode = 0;
      // this.clearCanvas();
      document.getElementById('maskInput').click();
    },
    uploadBackgroundClick() {
      this.mode = 0;
      // this.clearCanvas();
      document.getElementById('backgroundInput').click();
    },
    uploadBackgroundChange() {
      const file = document.getElementById('backgroundInput').files[0];
      const reader = new FileReader();
      if (file.type === 'image/jpeg' || file.type === 'image/png') {
        reader.readAsDataURL(file);
      }
      reader.onload = (e) => {
        const raster = new paper.Raster({
          source: e.target.result,
          position: paper.view.center,
          onLoad: () => {
            // 获取视图的最大宽度和高度
            var maxWidth = paper.view.size.width;
            var maxHeight = paper.view.size.height;
            // 计算适合的缩放比例，保持图片宽高比不变
            var scaleFactor = Math.min(maxWidth / raster.width, maxHeight / raster.height);
            // 如果 scaleFactor 小于 1，才进行缩放，避免放大图片
            if (scaleFactor < 1) {
              raster.scale(scaleFactor);
            }
            this.backgroundRaster = raster;
            // 确保 bottomRectangle 一直处于最底层
            this.backgroundRaster.insertBelow(paper.project.activeLayer);
            document.getElementById('backgroundInput').value = null;//清空input
          }
        });
      };
    },
    uploadMaskChange() {
      const file = document.getElementById('maskInput').files[0];
      const reader = new FileReader();
      if (file && file.type === 'image/jpeg' || file.type === 'image/png') {
        reader.readAsDataURL(file);
      }
      reader.onload = function (e) {
        const request = {
          image: e.target.result.split(',')[1]
        };
        // 发送 POST 请求到后端
        fetch(`http://${globalData.IP}:5000/preProcessUploadMask`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(request)
        })
          .then(response => response.json()) // 解析响应为 JSON
          .then(data => {
            this.exportCanvas(data.result);
            document.getElementById('maskInput').value = null;//清空input
          })
      }.bind(this);
    },
    //删除发射元素
    deleteEmit(assignId) {
      //删除控制点,以及linedetail对应项
      globalData.lineDetail = globalData.lineDetail.filter(line => {
        if (line.assignId === assignId) {
          this.removeControlPoints(line.lineId);
          this.removePointArea(line.lineId);
          return false;
        }
        return true;
      });

      //删除mappingdata对应项
      delete globalData.mappingData[assignId];
      //删除filterData的项
      globalData.lineDetail.forEach(detail => {
        if (detail['assignId'] === assignId) {
          const lineId = detail['lineId']
          delete globalData.filteredData[lineId];
        }
      });
      //删除按钮
      this.delMessage = this.delMessage.filter((message) => {
        if (message.assignId === assignId) {
          return false; // 过滤掉被移除的sign对象
        }
        return true; // 保留其他sign对象
      });
      //删除记录
      const index = globalData.emitDetail.findIndex(item => item.assignId === assignId)
      if (index !== -1) {
        globalData.emitDetail.splice(index, 1);
      }
      //处理line发射区
      this.emitLines.forEach(line => {
        line.assignId = line.assignId.filter(id => id !== assignId);
        if (line.assignId.length < 1) {
          line.opacity = 0;
        }
      });
      //处理mask发射区
      this.emitMasks.forEach(mask => {
        mask.assignId = mask.assignId.filter(id => id !== assignId);
        if (mask.assignId.length < 1) {
          mask.fillColor = 'black';
        }
      });
      //处理paths
      this.paths.forEach((path) => {
        path.assignId = path.assignId.filter(id => id !== assignId);
        //隐藏
        if (path.assignId.length == 0) {
          if (path.fillColor)
            path.fillColor = 'black';
          path.strokeColor = 'black';
        }
      })
      //处理发射标记
      this.emitAreaSigns = this.emitAreaSigns.filter((sign) => {
        if (sign.assignId === assignId) {
          sign.remove();
          return false; // 过滤掉被移除的sign对象
        }
        return true; // 保留其他sign对象
      });
      //处理可能轨迹
      for (let i = this.line_Paths.length - 1; i >= 0; i--) {
        if (this.line_Paths[i].assignId === assignId) {
          this.line_Paths[i].remove();
          this.line_Paths.splice(i, 1);  // 删除满足条件的元素
        }
      }
      //隐藏toast
      this.hideMappingToast();
    },
    //展示发射消息框函数
    showStrokeToast() {
      if (this.strokeToast != null) this.strokeToast.show();
    },
    //隐藏绘制消息框函数
    hideStrokeToast() {
      if (this.strokeToast != null) this.strokeToast.hide();
    },
    //展示mapping函数
    showMappingToast() {
      if (this.mappingToast != null) this.mappingToast.show();
    },
    //隐藏mapping函数
    hideMappingToast() {
      if (this.mappingToast != null) this.mappingToast.hide();
    },
    //展示maskToast函数
    showMaskToast() {
      if (this.maskToast != null) this.maskToast.show();
    },
    //隐藏maskToast函数
    hideMaskToast() {
      if (this.maskToast != null) this.maskToast.hide();
    },
    //展示linetoast函数
    showLineToast() {
      if (this.lineToast != null) this.lineToast.show();
    },
    //隐藏linetoast函数
    hideLineToast() {
      if (this.lineToast != null) this.lineToast.hide();
    },
    //隐藏所有黑黑的mask
    hideBlackThing() {
      this.paths.forEach((path) => {
        path.opacity = 0.1;
        if (path.fillColor)
          path.fillColor = 'black';
        path.strokeColor = 'black';
      })
      this.emitMasks.forEach((mask) => {
        mask.opacity = 0.1;
        mask.fillColor = 'black';
      })
    },
    //展示所有黑黑的mask
    showBlackThing() {
      this.paths.forEach((path) => {
        path.opacity = this.blackThingOpacity;
        if (path.assignId.length > 0) {
          if (path.fillColor)
            path.fillColor = new paper.Color(0, 95 / 255, 204 / 255);
          path.strokeColor = new paper.Color(0, 95 / 255, 204 / 255);
        }
      })

      this.emitMasks.forEach((mask) => {
        mask.opacity = this.blackThingOpacity;
        if (mask.assignId.length > 0) {
          mask.fillColor = new paper.Color(0, 95 / 255, 204 / 255);
        }
      })
    },
    //隐藏前景，保留背景
    hideCanvasForeground() {
      this.emitLines.forEach((line) => {
        line.opacity = 0;
      })
      this.emitPoints.forEach((point) => {
        point.opacity = 0;
      })
    },
    //展示前景
    showCanvasForeground() {
      //重新显示发射区
      this.emitLines.forEach((line) => {
        if (line.assignId.length > 0)
          line.opacity = 1;
      })
      this.emitPoints.forEach((point) => {
        point.opacity = 1;
      })
      this.paths.forEach(path => {
        if (path.assignId.length > 0) {
          if (path.fillColor)
            path.fillColor = new paper.Color(0, 95 / 255, 204 / 255);
          path.strokeColor = new paper.Color(0, 95 / 255, 204 / 255);
        }
      });

      this.emitMasks.forEach(mask => {
        if (mask.assignId.length > 0) {
          mask.fillColor = new paper.Color(0, 95 / 255, 204 / 255);
        }
      });
    },
    //展示轨迹
    showLineTrack() {
      this.line_Paths.forEach((path) => {
        path.opacity = 1;
        path.fullySelected = true;
        //控制点展示
        const pointsArray = this.controlPoints[path.lineId];
        if (pointsArray) {
          pointsArray.forEach(element => {
            element[0].opacity = 1;
            element[1].opacity = 1;
          });
        }
      })
      //开启动画
      this.updateAnimation();
    },
    //隐藏轨迹
    hideLineTrack() {
      this.line_Paths.forEach((path) => {
        path.opacity = 0;
        path.fullySelected = false;
        //控制点隐藏
        const pointsArray = this.controlPoints[path.lineId];
        if (pointsArray) {
          pointsArray.forEach(element => {
            element[0].opacity = 0;
            element[1].opacity = 0;
          });
        }
      })
      //关闭动画
      paper.view.onFrame = null;

    },
    //封闭路径函数
    closePath() {
      this.path.closed = true;
      this.path.finishDrawing = true;
      // 填充路径
      this.path.fillColor = 'black';
      this.path.opacity = this.blackThingOpacity;
      this.hideStrokeToast();
      this.exportCanvas();
      this.path = null;
    },
    //不封闭路径函数
    dontClosePath() {
      this.path.finishDrawing = true;
      this.path.opacity = this.blackThingOpacity;
      this.hideStrokeToast();
      this.exportCanvas();
      this.path = null;
    },

    //导出画布获得边界，生成发射区的函数
    exportCanvas(generateMask = false) {
      // 创建请求体对象
      var canvasHeight = this.canvas.offsetHeight;
      var canvasWidth = this.canvas.offsetWidth;
      var base64Data = ''
      if (generateMask) {
        base64Data = generateMask;
      }
      else {
        // 设置新 Canvas 
        const newCanvas = document.createElement('canvas');
        newCanvas.width = canvasWidth;
        newCanvas.height = canvasHeight;
        paper.setup(newCanvas);
        this.paths.forEach(path => {
          path.copyTo(paper.project.activeLayer);
        });
        this.emitMasks.forEach(mask => {
          mask.copyTo(paper.project.activeLayer);
        });
        // 渲染 Paper.js 画布内容
        paper.view.update(); // 更新视图以确保内容被渲染
        // 将画布内容转换为 PNG 数据 URL
        base64Data = newCanvas.toDataURL('image/png').split(',')[1];
      }

      const request = {
        canvasHeight: canvasHeight,
        canvasWidth: canvasWidth,
        image: base64Data,
        generateMask: generateMask ? true : false,
      };
      //重新activate主画布
      paper.projects[0].activate();
      // 发送 POST 请求到后端
      fetch(`http://${globalData.IP}:5000/generateEmitArea`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(request)
      })
        .then(response => response.json()) // 解析响应为 JSON
        .then(data => {
          // 处理响应数据
          if (data.status === 0) {
            //生成发射边界
            const boundaryList = data.boundary_points_list;
            if (boundaryList.length > 0) {
              for (var i = 0; i < boundaryList.length; i++) {

                const boundary = boundaryList[i];
                let newPath = new paper.Path({
                  strokeColor: 'rgba(0, 119, 255, 0.7)',
                  strokeWidth: 8,
                  opacity: 0,
                  boundaryIndex: data.boundary_index[i],//这个emitline所从属的areapoints的索引
                  isEmitArea: true,
                  assignId: [],
                  emitType: 'line',
                  areaId: this.areaCounter
                });
                this.areaCounter += 1;
                this.emitLines.push(newPath)

                let copyPath = newPath.clone();
                boundary.forEach((point) => {
                  copyPath.add(new paper.Point(point[0], point[1]));
                })
                let pointsArray = this.rebuildPathWithUniformPoints(copyPath, 100);
                // 遍历 pointsArray，将每个点添加到 newPath 中
                pointsArray.forEach(point => {
                  newPath.add(new paper.Point(point[0], point[1])); // 假设 pointsArray 中的每个元素是 [x, y]
                });
                copyPath.remove();
                newPath.onMouseEnter = (event) => {
                  if (newPath.assignId.length == 0 && !globalData.collaging) {
                    newPath.opacity = 1;
                  }
                };

                newPath.onMouseLeave = (event) => {
                  if (newPath.assignId.length == 0 && !globalData.collaging) {
                    newPath.opacity = 0;
                  }
                };
              }
            }
            const pointsList = data.points_list;
            if (pointsList.length > 0) {
              this.areaPoints = pointsList;
            }
            console.log(this.emitLines)

            if (generateMask) {
              //生成发射面
              const pointsList = data.points_list;
              pointsList.forEach(points => {
                let newPath = new paper.Path({
                  fillColor: 'black',
                  opacity: this.blackThingOpacity,
                  isEmitArea: true,
                  assignId: [],
                  emitType: 'mask',
                  areaId: this.areaCounter,
                  strokeWidth: 0
                });
                this.areaCounter += 1;
                this.emitMasks.push(newPath);
                points.forEach((point) => {
                  newPath.add(new paper.Point(point[0], point[1]));
                })

                newPath.onMouseEnter = (event) => {
                  if (newPath.assignId.length == 0 && !globalData.collaging) {
                    newPath.fillColor = new paper.Color(0, 95 / 255, 204 / 255);
                  }
                  if (this.mode == 2 && this.isDrawing) {
                    this.line_Path.strokeColor = '#4CAF50';
                    this.line_Path.areaId = newPath.areaId;
                    this.safe_place_release = true;
                  }
                };

                newPath.onMouseLeave = (event) => {
                  if (newPath.assignId.length == 0 && !globalData.collaging) {
                    newPath.fillColor = 'black';

                  }
                  if (this.mode == 2 && this.isDrawing) {
                    this.line_Path.strokeColor = '#FFC107';
                    this.line_Path.areaId = null;
                    this.safe_place_release = false;
                  }
                };


                newPath.onMouseUp = (event) => {
                  this.selectedMaskAreaId = newPath.areaId;
                  //一大段计算toast
                  const toast = document.getElementById("maskToast");
                  const toastContainer = document.querySelector(".maskToast-container");
                  // 计算 toastContainer 的位置
                  const viewPosition = paper.project.view.viewToProject(event.point);
                  const { x, y } = viewPosition;
                  this.nowX = x;
                  this.nowY = y;
                  let leftPos = x;
                  let topPos = y;
                  // 设置 toastContainer 的位置
                  toastContainer.style.left = Math.max(0, leftPos) + "px";
                  toastContainer.style.top = Math.max(0, topPos) + "px";
                  this.maskToast = new Toast(toast);
                  if (this.maskToast) {
                    this.showMaskToast();
                  }
                };
                newPath.bringToFront();
                this.path = newPath;
                this.paths.push(newPath);
              });
            }
          }

        })
        .catch(error => {
          // 处理错误
          console.error(error);
        });

    },
    //将绘制的路径归一化到20点
    rebuildPathWithUniformPoints(originalPath, numPoints) {
      let totalLength = originalPath.length; // 获取原始路径的总长度
      // let numPoints = Math.floor(totalLength / 30)
      let step = totalLength / numPoints; // 计算步长（每个点之间的距离）

      let pointsArray = []; // 创建一个数组来存储采样的点

      // 根据步长获取多个等距点
      for (let i = 0; i < numPoints; i++) {
        let offset = i * step; // 当前 offset，步长间隔
        let point = originalPath.getPointAt(offset); // 获取 offset 处的点

        if (point) {
          pointsArray.push([point.x, point.y]); // 将点的坐标添加到数组中
        }
      }

      // 手动添加终点，确保路径终点被包含
      let endPoint = originalPath.getPointAt(totalLength); // 获取路径的终点
      if (endPoint) {
        pointsArray.push([endPoint.x, endPoint.y]); // 添加终点的坐标
      }

      return pointsArray; // 返回点数组
    },
    //角度法判断点是否在轮廓内
    isPointInsidePolygon(point, polygon) {
      let x = point[0], y = point[1];
      let totalAngle = 0;

      for (let i = 0; i < polygon.length; i++) {
        let xi = polygon[i][0], yi = polygon[i][1];
        let xj = polygon[(i + 1) % polygon.length][0], yj = polygon[(i + 1) % polygon.length][1];

        let angle1 = Math.atan2(yi - y, xi - x);
        let angle2 = Math.atan2(yj - y, xj - x);
        let angle = angle2 - angle1;

        if (angle > Math.PI) angle -= 2 * Math.PI;
        if (angle < -Math.PI) angle += 2 * Math.PI;

        totalAngle += angle;
      }

      return Math.abs(totalAngle) > Math.PI;
    },
    prepareCollage() {
      fetch(`http://${globalData.IP}:5000/get_working`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        },
      })
        .then(response => response.json()) // 解析响应为 JSON
        .then(data => {
          if (data["working"]) {
            ElMessage({
              message: "busy..please wait",
              grouping: true,
              type: 'warning',
            })
          }
          else {
            globalData.collaging = true;
            // 获取当前时间戳（单位：毫秒）
            const timestamp = new Date().getTime();
            // 如果需要将时间戳转换为秒数，可以除以1000
            const timestampInSeconds = Math.floor(timestamp / 1000);
            globalData.processId = timestampInSeconds;

            // 设置新 Canvas,用来保存mask 
            const newCanvas = document.createElement('canvas');
            newCanvas.width = globalData.canvasWidth;
            newCanvas.height = globalData.canvasHeight;
            paper.setup(newCanvas);
            // 将 this.paths 中的路径添加到 Paper.js 的项目中
            this.paths.forEach(path => {
              path.copyTo(paper.project.activeLayer); // 将路径复制到新的项目图层中
            });
            // 将 this.paths 中的路径添加到 Paper.js 的项目中
            this.emitMasks.forEach(mask => {
              mask.copyTo(paper.project.activeLayer); // 将路径复制到新的项目图层中
            });

            // 渲染 Paper.js 画布内容
            paper.view.update(); // 更新视图以确保内容被渲染
            // 将画布内容转换为 PNG 数据 URL
            var base64Data = newCanvas.toDataURL('image/png').split(',')[1];
            globalData.mask = base64Data;

            //重新activate主画布
            // paper.projects[0].activate();
            EventBus.emit('startRealCollage', { data: '' });


          }
        })
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
        else if (newValue == 2) {
          this.btnOpacity['write-btn'] = 1;
        }
      },

    },
    collaging: {
      handler(newVal) {
        if (newVal) {
          Object.keys(this.controlPoints).forEach(key => {
            const controlPoint = this.controlPoints[key];
            if (controlPoint) {
              controlPoint.forEach(element => {
                element[0].opacity = 0;
                element[1].opacity = 0;
              });
            }
          });
          this.line_Paths.forEach(path => {
            path.fullySelected = false;
          });
          this.emitAreaSigns.forEach(element => {
            element.opacity = 0.3;
          });

          this.hideBlackThing();
        }
        else {
          Object.keys(this.controlPoints).forEach(key => {
            const controlPoint = this.controlPoints[key];
            if (controlPoint) {
              controlPoint.forEach(element => {
                element[0].opacity = 1;
                element[1].opacity = 1;
              });
            }
          });
          this.line_Paths.forEach(path => {
            path.fullySelected = true;
          });
          this.emitAreaSigns.forEach(element => {
            element.opacity = 1;
          });
          
        }
      },
      deep: true
    },
    globalData: {
      handler(newVal) {
        let flag = true;
        const emitDetail = newVal.emitDetail;
        const lineDetail = newVal.lineDetail;
        if (emitDetail.length < 1) {
          flag = false;
        }
        emitDetail.forEach(element => {
          if (!element.selectedVis) {//一旦有未选择selectedVis
            flag = false;
          }
          if (element.type != 'point' && !element.selectedData) {//一旦有未选择selectedData的非点元素
            flag = false;
          }
          if (element.type === 'point') {//检查点元素是否有线
            const assignId = element.assignId;
            let haveLine = false;
            lineDetail.forEach(line => {
              if (line.assignId === assignId) {
                haveLine = true;
              }
            });
            if (!haveLine) {
              flag = false;
            }
          }

        });
        lineDetail.forEach(element => {//检查线是否有数据
          if (!element.filteredData || element.filteredData.length < 1) {
            flag = false;
          }
        });
        globalData.okToCollage = flag;
        if(!globalData.okToCollage){
          this.showBlackThing();
        }

      },
      deep: true
    },
  },
};
</script>

<style>
@import "../assets/css/canvas.css";
@import "bootstrap/dist/css/bootstrap.min.css";
@import "bootstrap-icons/font/bootstrap-icons.css";
</style>
