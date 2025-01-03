<script setup>
import EventBus from "@/EventBus";
import globalData from "@/globalData";
import { ElMessage } from 'element-plus';
import paper from "paper";
</script>
<template>
    <div class="animation-container">
        <div v-if="globalData.collaging" class="progress" id="progress" role="progressbar"
            aria-label="Animated striped example" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">
            <div class="progress-bar progress-bar-striped"
                :class="progress == 100 ? 'bg-success' : 'progress-bar-animated'" :style="{ width: progress + '%' }">
                {{ progress }}%</div>
        </div>
        <div class="preview-container">
            <canvas class="aniCanvas" id="aniCanvas" draggable="false">
            </canvas>
            <img v-if="globalData.collageResult != ''" class="collageResult" :src="globalData.collageResult" :style="{
                width: resultWidth + 'px',
                height: resultHeight + 'px',
            }" />
            <!-- line类型可视化 -->
            <div v-show="item.type === 'line'" v-for="(item, index) in globalData.emitDetail" :key="index">
                <img v-if="item.selectedData && item.type === 'line' && !globalData.collaging"
                    v-for="(pos, i) in samplePoints(item.areaPoints, item.selectedData?.length)"
                    class="line-display-element" :src="globalData.emitDetail[index]['img']" :style="{
                        top: pos[1] + 'px',
                        left: pos[0] + 'px',
                        transform: 'translate(-50%, -50%)',
                        width: item?.renderWidth * 0.7 + 'px',
                        height: item?.renderHeight * 0.7 + 'px',
                        opacity: 0.7
                    }" />

            </div>
            <!-- 动画1 -->
            <div v-for="(item, index) in animation1_data" :key="index">
                <div v-for="(dataItem, i) in item.data" :key="i">
                    <img :src="item.img" :width="item.renderWidth * dataItem" :height="item.renderHeight * dataItem"
                        :data-value="dataItem" class="trace-element" :flag-value="item.flag[i]" :style="{
                            transform: 'translate(-50%, -50%) rotate(' + item.rotation[i] + 'deg)',
                            position: 'absolute',
                            left: item.trace[item.flag[i]][0] + 'px',
                            top: item.trace[item.flag[i]][1] + 'px',
                            transition: item.animation ? 'all ' + animation1Speed + 's linear' : '',
                            opacity: item.flag[i] === 0 || item.flag[i] === item.trace.length - 1 || firstAnimateOpacity === 0 ? 0 : 1,
                        }" />
                </div>
            </div>
        </div>
    </div>

</template>
<script>
export default {
    name: "animationComponent",
    computed: {
        lineDetail() {
            return globalData.lineDetail;
        }
    },
    data() {
        return {
            elements: [],
            canvas: null,
            old_lineDetail: null,
            progress: 0,
            processId: 0,
            progressTimer: null,
            //元素动画参数
            srcArray: [],
            posArray: [],
            widthArray: [],
            heightArray: [],
            angleArray: [],
            type: 'svg',
            resultWidth: 0,
            resultHeight: 0,
            animation1Speed: 0.5,
            animation2Speed: 10,
            animation3Speed: 2,
            firstAnimateOpacity: 1,//动画1全局透明度
            //三个阶段的数据
            animation3_data: [],
            animation2_data: null,
            animation1_data: {},
            animation1_timer: [],
            //三阶段进度
            animation1_progress: 0,
            animation2_progress: {},
            animation3_progress: {},
            //collage专门存储进度的数组
            collageProgress: [],
            //更新进度条的计时器
            updateProgressTimer: null,
            replayMode: false,
            lineIds: [],//看看本次collage有多少line，包括null line,
            activateLineIds: [], //开始2阶段的id
        };
    },
    mounted() {
        const canvas = document.getElementById("aniCanvas");
        this.canvas = canvas;
        EventBus.on('startRealCollage', this.startRealCollage);
        EventBus.on('stopCollage', this.stopCollage);
        EventBus.on('deleteCollageResult', this.resetData);
        EventBus.on('playAnimation1', this.continueAnimation1);
        EventBus.on('pauseAnimation1', this.pauseAnimation1);
        EventBus.on('replayCollage', this.replayCollage);
        EventBus.on('changeAnimationSpeed', (data) => {
            this.changeAnimationSpeed(data.speed)
        });

    },
    methods: {
        changeAnimationSpeed(speedRate) {
            this.animation1Speed = 0.5 / speedRate;
            this.animation2Speed = 10 / speedRate;
            this.animation3Speed = 2 / speedRate;
            if (!globalData.collaging) {
                this.continueAnimation1();
            }
            else {
                this.continueAnimation1();
                if (this.progressTimer) {
                    clearInterval(this.progressTimer)
                    this.progressTimer = setInterval(this.getProgress.bind(this), this.animation3Speed * 1000);
                    console.log('将现有fetch服务器数据的定时器更新为', this.progressTimer, this.animation3Speed * 1000)
                }
            }
        },
        //完整的reset
        resetData() {
            this.replayMode = false;
            globalData.collageResult = null;
            this.srcArray = [];
            this.posArray = [];
            this.widthArray = [];
            this.heightArray = [];
            this.angleArray = [];
            this.animation3_data = [];
            this.animation2_data = null;
            this.firstAnimateOpacity = 1;
            this.animation1_progress = 0;
            this.animation2_progress = {};
            this.animation3_progress = {};
            this.collageProgress = [];
            this.progressTimer = null;
            this.lineIds = [];
            this.progress = 0;
            this.elements = this.elements.filter(e => {
                e.remove();
                return false;
            })
            this.activateLineIds = [];
        },
        //保存上一次结果的reset
        resetReplayData() {
            this.animation1Speed = 0.5;
            this.animation2Speed = 10;
            this.animation3Speed = 2;
            this.activateLineIds = [];
            this.progress = 0;
            this.replayMode = true;
            this.firstAnimateOpacity = 1;
            this.animation1_progress = 0;
            this.animation2_progress = {};
            this.animation3_progress = {};
            this.progressTimer = null;
            this.elements = this.elements.filter(e => {
                e.remove();
                return false;
            })
            for (let i = 0; i < this.animation2_data['lineId'].length; i++) {
                this.posArray[i] = [(globalData.canvasWidth / 2) + this.animation2_data['origin_pos'][i][0], (globalData.canvasHeight / 2) + this.animation2_data['origin_pos'][i][1]];
                const detail = globalData.emitDetail.find(detail => detail.assignId === this.animation2_data['assignId'][i]);
                const longerEdge = detail['renderWidth'] > detail['renderHeight'] ? detail['renderWidth'] : detail['renderHeight']
                this.widthArray[i] = longerEdge + 20;
                this.heightArray[i] = longerEdge + 20;
                this.angleArray[i] = 0;
                const raster = new paper.Raster({
                    source: this.srcArray[i],
                    position: this.posArray[i],
                    lineId: this.animation2_data['lineId'][i],
                    data_index: i,
                    opacity: 0,
                    onLoad: () => {
                        raster.scale(this.widthArray[i] / raster.width);
                        this.elements.push(raster);
                    }
                });
            }


        },
        //停止动画1
        stopAnimation1() {
            Object.values(this.animation1_data).forEach(element => {
                const lineId = element['lineId'];
                this.clearLineTimer(lineId);
                this.animation1_data[lineId]['timer_status'] = false;
                this.animation1_data[element['lineId']]['flag'] = new Array(element['flag'].length).fill(0);
            });
        },
        //暂停动画1
        pauseAnimation1() {
            Object.values(this.animation1_data).forEach(element => {
                const lineId = element['lineId'];
                this.clearLineTimer(lineId);
                this.animation1_data[lineId]['timer_status'] = false;
            });
        },
        //继续动画1
        continueAnimation1() {
            Object.values(this.animation1_data).forEach(element => {
                this.startAnimation1Timer(element['lineId']);
            });
        },
        //进度更新定时器
        updateProgressOnTime() {
            this.updateProgressTimer = setInterval(() => {
                // 计算到达终点的元素个数
                let finish_ele_count = 0;
                let total_ele_count = 0;
                Object.values(this.animation1_data).forEach(element => {
                    const count = element.flag.filter(flag => flag === element.trace.length - 1).length;
                    finish_ele_count += count;
                    total_ele_count += element.flag.length;
                });
                if (total_ele_count > 0)
                    this.animation1_progress = finish_ele_count / total_ele_count
                else
                    this.animation1_progress = 1;

                this.progress = this.animation1_progress * 33 + 1;

                const lineIdNum = this.lineIds.length;
                // console.log(this.progress)
                let progress2 = 0;
                Object.values(this.animation2_progress).forEach(element => {
                    progress2 += element / lineIdNum;
                });
                // console.log(this.animation2_progress,progress2)
                this.progress += progress2 * 33;
                let progress3 = 0;
                Object.values(this.animation3_progress).forEach(element => {
                    progress3 += element / lineIdNum;
                });
                // console.log(this.animation3_progress,progress3)
                this.progress += progress3 * 33;
                this.progress = this.progress.toFixed(2); // 四舍五入到两位小数
                if (this.progress >= 100) {
                    setTimeout(() => {
                        clearInterval(this.updateProgressTimer)
                        globalData.collaging = false;
                        this.firstAnimateOpacity = 1;
                        paper.view.onFrame = null;
                        paper.view.pause();
                        this.stopAnimation1();
                    }, this.animation3Speed * 1000)

                }
            }, 2000);
        },
        //启动collage
        replayCollage() {
            paper.setup(this.canvas);
            globalData.collaging = true;
            this.resetReplayData();
            this.startAnimation1();
            this.updateProgressOnTime();
            //存在 null lineId
            for (let i = 0; i < this.lineIds.length; i++) {
                if (this.lineIds[i] == null) {
                    this.inventAnimate2(null);
                }
            }
        },
        startRealCollage() {
            paper.setup(this.canvas);
            console.log(this.canvas);
            this.resetData();
            this.startAnimation1();
            this.updateProgressOnTime();
            this.processId = globalData.processId;
            const request = {
                gravityEnable: globalData.gravityEnable,
                canvasHeight: globalData.canvasHeight,
                canvasWidth: globalData.canvasWidth,
                mask: globalData.mask,
                emitDetail: globalData.emitDetail,
                processId: globalData.processId,
                lineDetail: globalData.lineDetail
            };
            fetch(`http://${globalData.IP}:5000/collage`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(request)
            })
                .then(response => response.json()) // 解析响应为 JSON
                .then(data => {
                    if (data.status == 0 && globalData.collaging) {
                        // console.log(data)
                        this.animation2_data = data.result;
                        this.resultWidth = data.result['width'];
                        this.resultHeight = data.result['height'];
                        this.type = data.result['type'];
                        for (let i = 0; i < data.result['lineId'].length; i++) {
                            if (this.srcArray[i] == undefined) {
                                if (data.result['type'] == 'svg')
                                    this.srcArray[i] = `http://${globalData.IP}:5000/workdir/${globalData.processId}/outline_files/trans_uniform_${i + 1}.svg`
                                else
                                    this.srcArray[i] = `http://${globalData.IP}:5000/workdir/${globalData.processId}/outline_files/trans_uniform_${i + 1}.png`
                            }
                            this.posArray[i] = [(globalData.canvasWidth / 2) + data.result['origin_pos'][i][0], (globalData.canvasHeight / 2) + data.result['origin_pos'][i][1]];
                            const detail = globalData.emitDetail.find(detail => detail.assignId === data.result['assignId'][i]);
                            const longerEdge = detail['renderWidth'] > detail['renderHeight'] ? detail['renderWidth'] : detail['renderHeight']
                            this.widthArray[i] = longerEdge + 20;
                            this.heightArray[i] = longerEdge + 20;
                            this.angleArray[i] = 0;
                            const raster = new paper.Raster({
                                source: this.srcArray[i],
                                position: this.posArray[i],
                                lineId: data.result['lineId'][i],
                                data_index: i,
                                opacity: 0,
                                onLoad: () => {
                                    raster.scale(this.widthArray[i] / raster.width);
                                    this.elements.push(raster);
                                }
                            });
                        }
                        this.lineIds = Array.from(new Set(data.result['lineId']));
                        this.progressTimer = setInterval(this.getProgress.bind(this), this.animation3Speed * 1000);
                        //存在这个lineId
                        for (let i = 0; i < this.lineIds.length; i++) {
                            if (this.lineIds[i] == null) {
                                this.inventAnimate2(null);
                            }
                        }
                    }
                })
        },
        //点击stop按钮触发的停止
        stopCollage() {
            globalData.collaging = false;
            clearInterval(this.progressTimer);//删除取得process的定时器
            if (this.replayMode) {
                clearInterval(this.updateProgressTimer)
                globalData.collaging = false;
                this.firstAnimateOpacity = 1;
                paper.view.onFrame = null;
                paper.view.pause();
                this.stopAnimation1();
            } else {
                const request = {
                    id: globalData.processId
                };
                fetch(`http://${globalData.IP}:5000/stop_process`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(request)
                })
                    .then(response => response.json()) // 解析响应为 JSON
                    .then(data => {
                        // console.log(data);
                        clearInterval(this.updateProgressTimer)
                        globalData.collaging = false;
                        this.firstAnimateOpacity = 1;
                        paper.view.onFrame = null;
                        paper.view.pause();
                        this.stopAnimation1();
                    })
            }
        },
        // 获取进度的函数
        getProgress() {
            // 发送 GET 请求到后端
            fetch(`http://${globalData.IP}:5000/getProgress?id=${globalData.processId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
            })
                .then(response => response.json()) // 解析响应为 JSON
                .then(data => {
                    // 处理响应数据
                    // console.log(data);
                    if (data.status === 0) {
                        if (data["collage_result"]) {
                            clearInterval(this.progressTimer);
                            console.log('animation3_data finish push')
                            globalData.collageResult = `http://${globalData.IP}:5000/workdir/${globalData.processId}/final.${this.type}`;
                        }
                        if (data["result"]["pos"]?.length > 0) {//如果有结果了
                            this.animation3_data.push(data["result"]);
                            this.collageProgress.push({ 'steps': data['progress']['steps'], 'totalSteps': data['progress']['totalSteps'] })
                        }
                    }
                })
                .catch(error => {
                    // 处理错误
                    console.error(error);
                });
        },
        //真正设置动画1
        startAnimation1Timer(lineId) {
            //启动定时器
            const timer = setInterval(() => {
                // 更新 flag 数组，从 flag[0] 开始向后“传递”
                for (let i = 0; i < this.animation1_data[lineId].flag.length; i++) {
                    if (i === 0) {
                        // flag[0] 自增并取模 trace 长度
                        this.animation1_data[lineId].flag[i] = (this.animation1_data[lineId].flag[i] + 1) < this.animation1_data[lineId].trace.length ? this.animation1_data[lineId].flag[i] + 1 : this.animation1_data[lineId].trace.length - 1;
                    } else {
                        if (this.animation1_data[lineId].flag[i - 1] === 0) {
                            this.animation1_data[lineId].flag[i] = 0;
                        }
                        else if (this.animation1_data[lineId].flag[i - 1] > 0 && this.animation1_data[lineId].flag[i - 1] < this.animation1_data[lineId].trace.length - 1) {
                            this.animation1_data[lineId].flag[i] = this.animation1_data[lineId].flag[i - 1] - 1;
                        }
                        else if (this.animation1_data[lineId].flag[i - 1] === this.animation1_data[lineId].trace.length - 1) {
                            this.animation1_data[lineId].flag[i] = (this.animation1_data[lineId].flag[i] + 1) < this.animation1_data[lineId].trace.length ? this.animation1_data[lineId].flag[i] + 1 : this.animation1_data[lineId].trace.length - 1;
                        }
                    }
                }

                if (this.animation1_data[lineId].flag.every(flagValue => flagValue === this.animation1_data[lineId].trace.length - 1)) {//到达动画尽头
                    if (!globalData.collaging) {//如果不在collage就循环
                        // 等待1秒后执行
                        setTimeout(() => {
                            this.animation1_data[lineId].animation = false; // 关闭动画
                            this.animation1_data[lineId].flag = new Array(this.animation1_data[lineId].flag.length).fill(0); // 重置 flag
                            // 等待1秒后执行下一步
                            setTimeout(() => {
                                this.animation1_data[lineId].animation = true; // 重新启动动画
                            }, this.animation1Speed * 1000); // 第二个 setTimeout 延迟1秒
                        }, this.animation1Speed * 1000); // 第一个 setTimeout 是为了等待全部消失之后关闭动画，同时初始化位置
                    }
                    else {
                        if (!Object.keys(this.animation2_progress).includes(String(lineId))) {
                            console.log('还没有进行', lineId);
                            this.clearLineTimer(lineId);
                            this.animation1_timer[lineId] = null;
                            this.animation1_data[lineId]['timer_status'] = false;
                            this.inventAnimate2(lineId);
                        }
                    }
                } else {
                    if (globalData.collaging && this.animation2_data?.lineId?.length === this.elements.length && !this.replayMode) {
                        if (!Object.keys(this.animation2_progress).includes(String(lineId))) {
                            // 等待1秒后执行下一步
                            this.firstAnimateOpacity = 0;
                            this.clearLineTimer(lineId);
                            this.animation1_timer[lineId] = null;
                            this.animation1_data[lineId]['timer_status'] = false;
                            setTimeout(() => {
                                this.animation1_data[lineId].flag = new Array(this.animation1_data[lineId].flag.length).fill(this.animation1_data[lineId].trace.length - 1); //   flag 到终点
                                console.log('还没有进行', lineId);
                                this.inventAnimate2(lineId);
                            }, this.animation1Speed * 1000);
                        }
                    }
                }

            }, this.animation1Speed * 1000); // 每隔?秒更新
            this.clearLineTimer(lineId);
            console.log('startAnimation1', timer)
            this.animation1_timer[lineId] = timer;
            this.animation1_data[lineId]['timer_status'] = true;
        },
        updateAnimate(totalTime = 100, lineId) {

            for (let i = 0; i < this.elements.length; i++) {
                if (this.elements[i].lineId === lineId) {
                    this.elements[i].startPos = new paper.Point(this.elements[i].position);
                    this.elements[i].startRotate = this.elements[i].matrix.rotation;
                    this.elements[i].startScale = this.elements[i].matrix.scaling.x;
                    this.elements[i].endPos = new paper.Point(this.posArray[this.elements[i].data_index]);
                    this.elements[i].endRotate = this.angleArray[this.elements[i].data_index] * (180 / Math.PI);
                    this.elements[i].endScale = this.widthArray[this.elements[i].data_index] / this.elements[i].width;
                    this.elements[i].elapsedTime = 0;
                    this.elements[i].endOpacity = 1;
                    this.elements[i].startOpacity = this.elements[i].opacity;
                }
            }

            paper.view.onFrame = (event) => {
                for (let i = 0; i < this.elements.length; i++) {
                    if (this.activateLineIds.includes(String(this.elements[i].lineId))) {
                        const epsilon = 0.01; // 允许的误差范围
                        const pos = new paper.Point(this.elements[i].position);
                        const startPos = this.elements[i].startPos;
                        const endPos = this.elements[i].endPos;
                        const rotate = this.elements[i].matrix.rotation;
                        const opacity = this.elements[i].opacity;
                        const startOpacity = this.elements[i].startOpacity;
                        const endOpacity = this.elements[i].endOpacity;
                        const startRotate = this.elements[i].startRotate;
                        const endRotate = this.elements[i].endRotate;
                        const scale = this.elements[i].matrix.scaling.x;
                        const startScale = this.elements[i].startScale;
                        const endScale = this.elements[i].endScale;

                        this.elements[i].elapsedTime += event.delta; // 更新经过的时间
                        const t = Math.min(this.elements[i].elapsedTime / (totalTime / 1000), 1); // 插值比例，限制在 [0, 1]

                        if (Math.abs(opacity - endOpacity) > epsilon) {
                            const newOpacity = opacity + (endOpacity - startOpacity) / 200
                            this.elements[i].opacity = newOpacity;
                        }
                        if (Math.abs(pos.x - endPos.x) > epsilon || Math.abs(pos.y - endPos.y) > epsilon) {
                            const newPosition = [startPos.x + (endPos.x - startPos.x) * t, startPos.y + (endPos.y - startPos.y) * t]
                            this.elements[i].position = newPosition;
                        }
                        if (Math.abs(rotate - endRotate) > epsilon) {
                            const newRotate = startRotate + (endRotate - startRotate) * t
                            this.elements[i].rotate(newRotate - rotate);
                        }
                        if (Math.abs(scale - endScale) > epsilon) {
                            const newScale = startScale + (endScale - startScale) * t;
                            this.elements[i].scale(newScale / scale); // 相对缩放  
                        }

                    }
                }
            }
        },
        //设置动画2
        inventAnimate2(lineId) {
            const inventAnimate2Timer = setInterval(() => {
                const result = this.animation2_data;
                if (result && 'origin_pos' in result && result['lineId'].length === this.elements.length) {
                    clearInterval(inventAnimate2Timer);
                    for (let i = 0; i < result['lineId'].length; i++) {
                        if (result['lineId'][i] == lineId) {
                            this.posArray[i] = [(globalData.canvasWidth / 2) + result['des_pos'][i][0], (globalData.canvasHeight / 2) + result['des_pos'][i][1]];
                            if (result['type'] == 'svg') {
                                this.widthArray[i] = result['des_size'][i] * 100 * (result['width'] / 1000);
                                this.heightArray[i] = result['des_size'][i] * 100 * (result['height'] / 1000);
                            }
                            else {
                                this.widthArray[i] = result['des_size'][i] * 500 * (result['width'] / 1000);
                                this.heightArray[i] = result['des_size'][i] * 500 * (result['height'] / 1000);
                            }
                        }
                    }
                  
                    //动画2进度计时器（5秒线性增加）
                    ///////////////////////////////////////////////////////////////////
                    let elapsedTime = 0;             // 用于追踪已过去的时间
                    const timer = setInterval(() => {
                        elapsedTime += 100;     // 每次更新增加已过去的时间
                        // 计算当前进度，确保值在 0 到 1 之间
                        this.animation2_progress[lineId] = Math.min(elapsedTime / (this.animation2Speed * 1000), 1);
                        // 如果变量值已经到达 1，停止定时器
                        if (this.animation2_progress[lineId] >= 1 || !globalData.collaging) {
                            clearInterval(timer);
                        }
                    }, 100);
                    ///////////////////////////////////////////////////////////////////
                    this.activateLineIds.push(String(lineId));
                    // if(this.replayMode===false)
                    this.updateAnimate(this.animation2Speed * 1000, lineId);
                    this.inventAnimate3(lineId);
                }
            }, 200);
        },
        //设置动画3
        inventAnimate3(lineId) {
            function processCollageData(i = 0) {
                if (globalData.collaging) {
                    //更新速率应该与从后台拿去数据的速率相近
                    let waitTime = 0;
                    if (i != 0) waitTime = this.animation3Speed * 1000;
                    if (i >= this.animation3_data.length) { return; }//结束

                    this.animation3_progress[lineId] = this.collageProgress[i]['steps'] / this.collageProgress[i]['totalSteps'];

                    setTimeout(() => {
                        let result = this.animation3_data[i];
                        for (let j = 0; j < result['pos'].length; j++) {
                            if (lineId == result['lineId'][j]) {
                                this.posArray[j] = [(globalData.canvasWidth / 2) + result['pos'][j][0], (globalData.canvasHeight / 2) + result['pos'][j][1]];
                                this.angleArray[j] = result['angle'][j];
                                if (result['type'] == 'svg') {
                                    this.widthArray[j] = result['size'][j][0] * 100 * (result['width'] / 1000);
                                    this.heightArray[j] = result['size'][j][0] * 100 * (result['height'] / 1000);
                                }
                                else {
                                    this.widthArray[j] = result['size'][j][0] * 500 * (result['width'] / 1000);
                                    this.heightArray[j] = result['size'][j][0] * 500 * (result['height'] / 1000);
                                }
                            }
                        }
                        this.updateAnimate(this.animation3Speed * 1000, lineId);
                        processCollageData.call(this, i + 1);
                    }, waitTime);
                }
            }
            const inventAnimate3Timer = setInterval(() => {
                const lineIdNum = this.lineIds.length;
                // console.log(this.progress)
                let progress2 = 0;
                Object.values(this.animation2_progress).forEach(element => {
                    progress2 += element / lineIdNum;
                });
                //有足够的长度再执行
                if (this.animation3_data.length > 3 && progress2 === 1) {
                    // 启动处理函数
                    processCollageData.call(this);
                    clearInterval(inventAnimate3Timer);
                }
            }, 200);
        },
        //删除对应line动画
        clearLineTimer(lineId) {
            if (this.animation1_timer[lineId]) {
                clearInterval(this.animation1_timer[lineId]);
                console.log('旧定时器已清除', this.animation1_timer[lineId]);
                this.animation1_timer[lineId] = null;
            }
        },
        samplePoints(points, x) {
            if (x >= points.length) {
                return points; // 如果 x 大于等于点数量，返回全部点
            }

            const step = Math.floor(points.length / x);
            let sampledPoints = [];

            for (let i = 0; i < points.length; i += step) {
                if (sampledPoints.length < x) {
                    sampledPoints.push(points[i]);
                }
            }
            return sampledPoints;
        },
        //对所有line动画进行重启，包括位置的初始化
        startAnimation1() {
            Object.values(this.animation1_data).forEach(element => {
                this.animation1_data[element['lineId']]['flag'] = new Array(element['flag'].length).fill(0);
                this.startAnimation1Timer(element['lineId']);

            });
        },
        //对特定的line设置动画数据
        inventAnimate1(val) {
            if (val['filteredData'] && val['filteredData'].length > 0) {
                //准备数据
                var img = globalData.emitDetail.find(detail => detail.assignId === val.assignId)['img'];
                var renderWidth = globalData.emitDetail.find(detail => detail.assignId === val.assignId)['renderWidth'];
                var renderHeight = globalData.emitDetail.find(detail => detail.assignId === val.assignId)['renderHeight'];
                var data = val['filteredData']
                var normalizedData = null;
                if (typeof data[0] === 'string') {

                    normalizedData = new Array(data.length).fill(0.5);
                }
                else {
                    // 找到数据的最大值和最小值
                    var max = Math.max(...data);
                    var min = Math.min(...data);
                    // 使用归一化公式将数据缩放到 [0, 1] 范围
                    if (max === min) {
                        // 如果只有一个元素，直接返回一个正常值或其他逻辑
                        normalizedData = data.map(() => 0.5); // 例如，全部返回0.5
                    } else {
                        normalizedData = data.map(value => ((value - min) / (max - min)) * 0.5 + 0.5);
                    }
                }
                var rotation = new Array(data.length);
                for (let i = 0; i < data.length; i++) {
                    rotation[i] = Math.floor(Math.random() * 360);
                }
                var flag = new Array(data.length).fill(0);
                var trace = val['trace']

                this.animation1_data[val.lineId] = { 'lineId': val.lineId, 'animation': true, 'img': img, 'data': normalizedData, 'trace': trace, 'flag': flag, 'renderWidth': renderWidth, 'renderHeight': renderHeight, 'rotation': rotation, 'timer_status': false }

                this.startAnimation1Timer(val.lineId)

            }
        },


    },
    watch: {
        // 使用深度监听来检测 lineDetail 数组的变化
        lineDetail: {
            handler(newVal) {
                console.log('linedetail change')
                this.resetData();//改变了之前的结果就没有了
                //如果新的lineDetail为空
                if (newVal.length === 0) {
                    this.animation1_timer.forEach(element => {
                        if (element)
                            clearInterval(element);
                    });
                    this.animation1_data = {}
                    this.animation1_timer = []
                    return;
                }
                //如果新的lineDetail更少
                if (newVal?.length < this.old_lineDetail?.length) {
                    const newLineIds = new Set(newVal?.map(item => item.lineId));
                    const changedItems = this.old_lineDetail?.filter(item => !newLineIds.has(item.lineId));
                    this.clearLineTimer(changedItems[0].lineId);
                    delete this.animation1_data[changedItems[0].lineId];
                }
                //如果新的lineDetail更多
                else if (newVal?.length > this.old_lineDetail?.length) {
                    const oldLineIds = new Set(this.old_lineDetail?.map(item => item.lineId));
                    const changedItems = newVal.filter(item => !oldLineIds.has(item.lineId));
                    this.inventAnimate1(changedItems[0]);
                }
                //如果新的lineDetail跟原来数量一样
                else if (newVal?.length === this.old_lineDetail?.length) {
                    newVal.forEach((val, index) => {
                        if (
                            JSON.stringify(val.filteredData) !== JSON.stringify(this.old_lineDetail[index]?.filteredData) ||
                            JSON.stringify(val.trace) !== JSON.stringify(this.old_lineDetail[index]?.trace)
                        ) {
                            this.clearLineTimer(val.lineId);
                            delete this.animation1_data[val.lineId];
                            this.inventAnimate1(val);
                        }
                    });
                }
                this.old_lineDetail = JSON.parse(JSON.stringify(newVal));
            },
            deep: true, // 监听数组内部的变化
        }
    }
};
</script>
<style>
@import "../assets/css/animation.css";
</style>
