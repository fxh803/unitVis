<script setup>
import EventBus from "@/EventBus";
import globalData from "@/globalData";
import { ElMessage } from 'element-plus'
</script>
<template>
    <div class="collage-container">
        <button v-if="!globalData.collaging" id="collage-btn" type="button" class="btn btn-success collage-btn"
            @click="startCollage">
            start collage
        </button>
        <button v-if="globalData.collaging" id="stop-collage-btn" type="button" class="btn btn-danger stop-collage-btn"
            @click="stopCollage">
            {{!replayMode? 'stop collage':'stop replay'}}
        </button>

        <el-icon class="collage-play" @click="playAnimation1"
            v-if="globalData.lineDetail.length > 0 && !globalData.collaging && !playingAnimation1">
            <VideoPlay />
        </el-icon>
        <el-icon class="collage-pause" @click="pauseAnimation1"
            v-if="globalData.lineDetail.length > 0 && !globalData.collaging && playingAnimation1">
            <VideoPause />
        </el-icon>

        <svg v-if="globalData.collageResult && !globalData.collaging" t="1731986199707" class="icon replay-btn" @click="replayCollage" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="4269" width="16" height="16"><path d="M479.731512 967.155512c-50.051122 0-99.402927-8.192-146.65678-24.276292-48.452683-16.483902-93.608585-40.96-134.069073-72.629074C35.665171 742.375024-20.380098 520.192 62.538927 330.077659 134.868293 164.039805 298.60839 56.844488 479.531707 56.844488c23.876683 0 48.053073 1.898146 71.729952 5.694439 199.305366 31.669073 353.255024 190.613854 379.629268 389.419707l10.489756-10.489756c6.393756-6.193951 14.885463-9.590634 23.876683-9.590634 9.191024 0 17.782634 3.596488 24.276293 10.090146 13.187122 13.187122 13.287024 34.666146 0.399609 48.053073L915.406049 564.44878c-6.393756 6.393756-15.185171 10.090146-24.276293 10.090147-9.091122 0-17.882537-3.69639-24.276293-10.090147l-74.427317-74.427317c-12.887415-13.386927-12.68761-34.965854 0.39961-48.053073 6.493659-6.493659 15.085268-10.090146 24.276293-10.090146 8.891317 0 17.383024 3.396683 23.77678 9.590634l22.378147 22.378146C842.377366 296.810146 715.701073 161.841951 548.364488 131.671415c-22.677854-4.096-45.85522-6.193951-68.832781-6.193952-151.352195 0-289.517268 89.212878-352.056195 227.178147-73.128585 161.642146-27.273366 351.656585 111.591025 462.04878 68.133463 54.147122 153.550049 83.918049 240.565073 83.918049 85.61639 0 166.737171-27.473171 234.770731-79.422439 5.994146-4.595512 13.287024-7.093073 20.87961-7.093073 10.789463 0 20.679805 4.89522 27.273366 13.486829 11.48878 14.985366 8.59161 36.564293-6.393756 48.053073-40.060878 30.670049-84.617366 54.247024-132.270829 70.131512-46.554537 15.58478-95.00722 23.377171-144.15922 23.377171z m-42.158829-273.532878c-6.893268 0-13.886439-1.598439-20.08039-4.695414-15.285073-7.592585-24.775805-22.977561-24.775805-40.060879V375.233561c0-17.083317 9.490732-32.468293 24.775805-40.060878 6.193951-3.096976 13.08722-4.695415 20.08039-4.695415 9.590634 0 19.181268 3.196878 26.873756 8.99122L646.868293 476.135024c11.189073 8.391805 17.882537 21.778732 17.882536 35.864976 0 13.986341-6.693463 27.473171-17.882536 35.864976L464.446439 684.631415c-7.692488 5.794341-17.18322 8.99122-26.873756 8.991219z m23.77678-92.409756l118.983805-89.212878-118.983805-89.212878v178.425756z" fill="#2c2c2c" p-id="4270"></path></svg>
        <el-icon class="collage-clear" v-if="globalData.collageResult && !globalData.collaging"
            @click="deleteCollageResult">
            <Delete />
        </el-icon>
        <el-popover placement="right" :popper-style="{
            width: '250px',
            display: 'flex',
            flexDirection: 'column',
            fontSize: '12px'
        }" trigger="click">
            <template #reference>
                <el-icon class="collage-option">
                    <Setting />
                </el-icon>
            </template>
            <div class="gravity-enable">
                <span class="demonstration">gravity enable</span>
                <el-switch v-model="gravityEnable" class="mb-2" />
            </div>
            <div class="animation-speed">
                <span class="demonstration">animation speed</span>
                <el-slider  class="slider" v-model="animationSpeed" :step="25" show-stops :format-tooltip="formatSpeed" @change="changeAnimationSpeed()"/>
            </div>
        </el-popover>
    </div>
</template>

<script>
export default {
    name: 'collageComponent',

    data() {
        return {
            gravityEnable: false,
            playingAnimation1: true,
            animationSpeed: 1,
            replayMode:false
        };
    },
    mounted() {

    },
    methods: {
        startCollage() {
            this.replayMode = false;
            this.playingAnimation1 = false;
            globalData.gravityEnable = this.gravityEnable;
            EventBus.emit('prepareCollage', { data: '' });
        },
        stopCollage() {
            EventBus.emit('stopCollage', { data: '' });
        },
        deleteCollageResult() {
            globalData.collageResult = null;
            EventBus.emit('deleteCollageResult', { data: '' });
        },
        playAnimation1() {
            this.playingAnimation1 = true;
            EventBus.emit('playAnimation1', { data: '' });
        },
        pauseAnimation1() {
            this.playingAnimation1 = false;
            EventBus.emit('pauseAnimation1', { data: '' });
        },
        replayCollage(){
            this.replayMode = true;
            EventBus.emit('replayCollage', { data: '' });
        },
        formatSpeed(){
            return (this.animationSpeed/50+1).toFixed(1)
        },
        changeAnimationSpeed(){
            const speed = (this.animationSpeed/50+1).toFixed(1);
            EventBus.emit('changeAnimationSpeed', { 'speed': speed });
        },
    }
}
</script>

<style>
@import '../assets/css/collage.css';
</style>