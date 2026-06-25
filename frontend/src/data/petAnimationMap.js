// State→GIF mapping built from actual files in public/pets/default/
// Each state pool lists GIF filenames; idle is the universal fallback.

const IDLE = ['yes.gif', '无语.gif', '吐舌.gif', '吃薯片.gif', '浇水.gif']

export const PET_STATE_POOLS = {
  idle: IDLE,
  happy: ['点赞.gif', '鼓掌.gif', '喜欢.gif', '喜欢2.gif', '喜欢3.gif', '对手指.gif', '噗呲偷笑.gif'],
  excellent: ['举牌100分.gif', '鼓掌.gif', '喜欢3.gif', '灵光.gif'],
  thinking: ['思考.gif', '疑惑.gif', '端详.gif'],
  wrong: ['傻眼流口水.gif', '尴尬扣脸.gif', '拉泪.gif', '慌.gif', '比x.gif'],
  comfort: ['抱抱.gif', '拉泪.gif', '捏鼻.gif'],
  rest: ['喝茶休息.gif', '喝奶茶休息.gif', '纸箱休息.gif', '吃薯片.gif'],
  work: ['上工.gif', '灵光.gif', '我擦屏幕.gif'],
  message: ['震惊.gif', '疑惑.gif', '点赞.gif'],
  adventure: ['上工.gif', '纸箱休息.gif', '戳戳.gif'],
  returnReward: ['喜欢.gif', '点赞.gif', '举牌100分.gif', '鼓掌.gif'],
  click: ['抱抱.gif', '捏鼻.gif', '戳戳.gif', '坏笑.gif'],
  drag: ['拖动捏脸.gif'],
  annoyed: ['生气.gif', '无语.gif', '尴尬扣脸.gif', '哼哼.gif'],
}

export function pickGif(state) {
  const pool = PET_STATE_POOLS[state] || PET_STATE_POOLS.idle
  const idx = Math.floor(Math.random() * pool.length)
  return `/pets/default/${pool[idx]}`
}

export const TMP_STATE_DEFAULTS = {
  happy: 4000,
  excellent: 4000,
  thinking: 3000,
  wrong: 3500,
  comfort: 3500,
  message: 4000,
  returnReward: 4000,
  click: 3000,
  drag: 2000,
  annoyed: 3500,
}
