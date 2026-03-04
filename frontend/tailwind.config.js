export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        navy: { 900: '#0D1F3C', 800: '#1A3660', 700: '#1E5FA8' },
        brand: { DEFAULT: '#2E9CDB', light: '#7EC8E3' },
        gold: { DEFAULT: '#E5A700', light: '#F5C842' }
      }
    }
  },
  plugins: []
}
