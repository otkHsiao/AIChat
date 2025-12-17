import {
  createLightTheme,
  createDarkTheme,
  BrandVariants,
} from '@fluentui/react-components'

// Custom brand colors based on Azure blue
const brandColors: BrandVariants = {
  10: '#001f3f',
  20: '#003366',
  30: '#00478a',
  40: '#005ca8',
  50: '#0070c0',
  60: '#0078d4', // Azure primary blue
  70: '#1a88dc',
  80: '#3899e4',
  90: '#55aaec',
  100: '#73bbf3',
  110: '#91ccf9',
  120: '#b0ddff',
  130: '#cfedff',
  140: '#e8f6ff',
  150: '#f5fbff',
  160: '#ffffff',
}

export const lightTheme = createLightTheme(brandColors)
export const darkTheme = createDarkTheme(brandColors)

// Custom theme overrides
lightTheme.colorBrandForeground1 = brandColors[60]
lightTheme.colorBrandBackground = brandColors[60]

darkTheme.colorBrandForeground1 = brandColors[80]
darkTheme.colorBrandBackground = brandColors[70]