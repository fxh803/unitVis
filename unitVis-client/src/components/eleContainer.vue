<script setup>
import paper from "paper";
import globalData from "@/globalData";
import EventBus from "@/EventBus";
</script>
<template>
  <div class="elements-container" draggable="false">
    <div class="elements-wrapper" draggable="false">
      <img v-for="(key, index) in elementsIndex" :key="index" class="element-img" :src="getImgUrl(key)" draggable="true"
        @dragstart="onElementDragstart" />
      <img v-for="(ele, index) in uploadElements" :key="index" class="element-img" :src="ele" draggable="true"
        @dragstart="onElementDragstart" />
      <button type="button" class="btn btn-light addBtn" @click="uploadElementsClick">
        <i class="bi bi-plus-square-dotted"></i>
        <input type="file" id="elementsInput" accept=".svg, .png" @change="uploadElementsChange" multiple />
      </button>
    </div>
    <div class="empty-div"></div>
  </div>
</template>

<script>
export default {
  name: "eleContainerComponent",
  data() {
    return {
      elementsIndex: [],
      uploadElements: [],
    };
  },
  mounted() {
    this.elementsIndex = Array.from({ length: 9 }, (_, index) => index);
   },

  methods: {
    getImgUrl(key) {
      return `src/assets/elements/${key}.svg`;
    },
    onElementDragstart(event) {
      globalData.draggingEle= true;
      paper.projects[0].activate();
      const imageUrl = event.target.src;
      event.dataTransfer.setData('text/plain', imageUrl);
      const x = event.clientX;
      const y = event.clientY; 
      event.dataTransfer.setData('text/positionX', JSON.stringify(x));
      event.dataTransfer.setData('text/positionY', JSON.stringify(y));
    },
    uploadElementsClick() {
      document.getElementById('elementsInput').click();
    },
    uploadElementsChange() {
      const files = document.getElementById('elementsInput').files;
      for (let i = 0; i < files.length; i++) {
        const reader = new FileReader();
        reader.onload = function (e) {
          this.uploadElements.push(e.target.result); // 将每个文件的结果存储在数组中
        }.bind(this); // 绑定上下文以在回调中访问this.uploadElements

        if (files[i].type === 'image/svg+xml' || files[i].type === 'image/png') {
          reader.readAsDataURL(files[i]);
        } else {
          alert('Please upload valid SVG or PNG files.');
        }
      }
    },
  },
};
</script>

<style>
@import "../assets/css/eleContainer.css";
</style>
