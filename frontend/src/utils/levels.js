const MAJOR_LEVELS = {
  '初级': ['萌新小白', '勤学学徒', '达标选手'],
  '中级': ['稳扎玩家', '进阶干将', '学科达人'],
  '高级': ['专业先锋', '满级学神'],
}

export function calcMajorLevel(subLevel) {
  for (const [major, subs] of Object.entries(MAJOR_LEVELS)) {
    if (subs.includes(subLevel)) return major
  }
  return '初级'
}

export const LEVEL_TIERS = [
  { name: '萌新小白', exp: [0, 199], major: '初级', color: 'from-gray-400 to-gray-500', icon: 'fas fa-seedling' },
  { name: '勤学学徒', exp: [200, 499], major: '初级', color: 'from-teal-400 to-cyan-500', icon: 'fas fa-book' },
  { name: '达标选手', exp: [500, 899], major: '初级', color: 'from-green-400 to-emerald-500', icon: 'fas fa-check-circle' },
  { name: '稳扎玩家', exp: [900, 1399], major: '中级', color: 'from-blue-400 to-indigo-500', icon: 'fas fa-gamepad' },
  { name: '进阶干将', exp: [1400, 1999], major: '中级', color: 'from-purple-400 to-violet-500', icon: 'fas fa-bolt' },
  { name: '学科达人', exp: [2000, 2699], major: '中级', color: 'from-indigo-400 to-purple-500', icon: 'fas fa-award' },
  { name: '专业先锋', exp: [2700, 3499], major: '高级', color: 'from-orange-400 to-red-500', icon: 'fas fa-rocket' },
  { name: '满级学神', exp: [3500, Infinity], major: '高级', color: 'from-amber-400 to-yellow-500 via-red-500', icon: 'fas fa-crown' },
]
