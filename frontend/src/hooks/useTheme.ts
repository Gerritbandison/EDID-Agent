import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface ThemeState {
  isDark: boolean
  toggle: () => void
  setDark: (isDark: boolean) => void
}

export const useTheme = create<ThemeState>()(
  persist(
    (set) => ({
      isDark: false,
      toggle: () => set((state) => {
        const newIsDark = !state.isDark
        document.documentElement.classList.toggle('dark', newIsDark)
        return { isDark: newIsDark }
      }),
      setDark: (isDark: boolean) => {
        document.documentElement.classList.toggle('dark', isDark)
        set({ isDark })
      },
    }),
    {
      name: 'theme-storage',
      onRehydrateStorage: () => (state) => {
        if (state?.isDark) {
          document.documentElement.classList.add('dark')
        }
      },
    }
  )
)
