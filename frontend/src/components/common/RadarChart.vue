<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  dimensions: { type: Array, required: true },
})

const hoveredIdx = ref(-1)

const cx = 160
const cy = 155
const radius = 120
const levels = 5

const angleStep = (2 * Math.PI) / props.dimensions.length

function angle(i) {
  return -Math.PI / 2 + i * angleStep
}

function polar(r, i) {
  const a = angle(i)
  return { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) }
}

// Grid polygons (one per level)
const gridPolygons = computed(() => {
  const result = []
  for (let lev = 1; lev <= levels; lev++) {
    const r = (radius / levels) * lev
    const pts = props.dimensions.map((_, i) => {
      const p = polar(r, i)
      return `${p.x},${p.y}`
    }).join(' ')
    result.push({ level: lev, points: pts })
  }
  return result
})

// Score polygon
const scorePoints = computed(() => {
  return props.dimensions.map((d, i) => {
    const r = (d.score / 100) * radius
    const p = polar(r, i)
    return `${p.x},${p.y}`
  }).join(' ')
})

// Axis lines (center to each vertex)
const axes = computed(() => {
  return props.dimensions.map((_, i) => {
    const p = polar(radius, i)
    return { x2: p.x, y2: p.y }
  })
})

// Label positions
const labels = computed(() => {
  return props.dimensions.map((d, i) => {
    const p = polar(radius + 28, i)
    return { ...p, name: d.name }
  })
})

// Score dot positions
const dots = computed(() => {
  return props.dimensions.map((d, i) => {
    const r = (d.score / 100) * radius
    return polar(r, i)
  })
})

function onHover(idx) {
  hoveredIdx.value = idx
}

function onLeave() {
  hoveredIdx.value = -1
}

const tooltipStyle = computed(() => {
  if (hoveredIdx.value < 0) return { display: 'none' }
  const d = props.dimensions[hoveredIdx.value]
  const dot = dots.value[hoveredIdx.value]
  return {
    display: 'block',
    left: dot.x + 'px',
    top: (dot.y - 10) + 'px',
  }
})

const tooltipData = computed(() => {
  if (hoveredIdx.value < 0) return null
  return props.dimensions[hoveredIdx.value]
})
</script>

<template>
  <div class="radar-wrapper">
    <svg :viewBox="`0 0 ${cx * 2} ${cy * 2 + 10}`" class="radar-svg">
      <!-- Grid polygons -->
      <polygon
        v-for="gp in gridPolygons"
        :key="gp.level"
        :points="gp.points"
        :fill="gp.level % 2 === 0 ? '#f8fafc' : '#f1f5f9'"
        :stroke="gp.level === levels ? '#cbd5e1' : '#e2e8f0'"
        stroke-width="1"
      />
      <!-- Axis lines -->
      <line
        v-for="(ax, i) in axes"
        :key="'ax' + i"
        :x1="cx" :y1="cy"
        :x2="ax.x2" :y2="ax.y2"
        stroke="#e2e8f0"
        stroke-width="1"
      />
      <!-- Score polygon -->
      <polygon
        :points="scorePoints"
        fill="rgba(99, 102, 241, 0.18)"
        stroke="rgba(99, 102, 241, 0.7)"
        stroke-width="2"
        stroke-linejoin="round"
      />
      <!-- Score dots -->
      <circle
        v-for="(dot, i) in dots"
        :key="'dot' + i"
        :cx="dot.x" :cy="dot.y" r="5"
        fill="#6366f1"
        stroke="#fff"
        stroke-width="2"
        :style="{ cursor: 'pointer' }"
        @mouseenter="onHover(i)"
        @mouseleave="onLeave"
      />
      <!-- Invisible wide hit areas for axes -->
      <line
        v-for="(ax, i) in axes"
        :key="'hit' + i"
        :x1="cx" :y1="cy"
        :x2="ax.x2" :y2="ax.y2"
        stroke="transparent"
        stroke-width="40"
        style="cursor: pointer"
        @mouseenter="onHover(i)"
        @mouseleave="onLeave"
      />
      <!-- Labels -->
      <text
        v-for="(lbl, i) in labels"
        :key="'lbl' + i"
        :x="lbl.x" :y="lbl.y"
        text-anchor="middle"
        dominant-baseline="middle"
        class="radar-label"
        :fill="hoveredIdx === i ? '#4f46e5' : '#475569'"
        :style="{ cursor: 'pointer', fontWeight: hoveredIdx === i ? 800 : 600 }"
        @mouseenter="onHover(i)"
        @mouseleave="onLeave"
      >{{ lbl.name }}</text>
      <!-- Center score text -->
      <text :x="cx" :y="cy - 6" text-anchor="middle" class="radar-center-score">
        {{ Math.round(dimensions.reduce((s, d) => s + d.score, 0) / dimensions.length) }}
      </text>
      <text :x="cx" :y="cy + 17" text-anchor="middle" class="radar-center-sub">
        综合均分
      </text>
    </svg>

    <!-- Tooltip -->
    <div class="radar-tooltip" :style="tooltipStyle" v-if="tooltipData">
      <p class="tooltip-title">{{ tooltipData.name }}：<strong>{{ tooltipData.score }}</strong> 分</p>
      <p class="tooltip-sources-label">分数来源：</p>
      <ul>
        <li v-for="src in tooltipData.sources" :key="src">{{ src }}</li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.radar-wrapper {
  position: relative;
  width: 100%;
  max-width: 420px;
  margin: 0 auto;
}
.radar-svg {
  width: 100%;
  height: auto;
  display: block;
}
.radar-label {
  font-size: 13px;
  transition: fill 0.15s, font-weight 0.15s;
}
.radar-center-score {
  font-size: 26px;
  font-weight: 900;
  fill: #4f46e5;
}
.radar-center-sub {
  font-size: 11px;
  fill: #94a3b8;
}

.radar-tooltip {
  position: absolute;
  transform: translate(-50%, -110%);
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 16px;
  min-width: 180px;
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.12);
  pointer-events: none;
  z-index: 10;
}
.tooltip-title {
  color: #1e293b;
  font-size: 14px;
  margin-bottom: 6px;
}
.tooltip-title strong {
  color: #4f46e5;
  font-weight: 900;
}
.tooltip-sources-label {
  color: #94a3b8;
  font-size: 11px;
  margin-bottom: 4px;
}
.radar-tooltip ul {
  margin: 0;
  padding: 0;
  list-style: none;
}
.radar-tooltip li {
  color: #475569;
  font-size: 12px;
  padding: 2px 0;
}
.radar-tooltip li::before {
  content: '· ';
  color: #6366f1;
  font-weight: bold;
}
</style>
