import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { CV_TEMPLATES } from "../data/cvTemplates";
import { SAMPLE_EDUCATIONS, SAMPLE_EXPERIENCES, SAMPLE_SKILLS } from "../data/sampleCvData";

export interface ExperienceItem {
  id: string;
  role: string;
  company: string;
  startDate: string;
  endDate: string;
  description: string;
}

export interface EducationItem {
  id: string;
  degree: string;
  school: string;
  startDate: string;
  endDate: string;
  gpa: string;
}

export interface PersonalInfo {
  fullName: string;
  title: string;
  email: string;
  phone: string;
  location: string;
  website: string;
  avatar: string;
  summary: string;
}

export type CvPersonalInfo = PersonalInfo;
export type CvExperience = ExperienceItem;
export type CvEducation = EducationItem;

export interface CvDraftState {
  // Gallery & Filter State (Client-only UI)
  selectedCategory: string;
  selectedLanguage: string;
  templateColors: Record<string, string>;

  // Builder State
  templateId: string;
  activeColor: string;
  activeTab: "info" | "experience" | "education" | "skills";
  personalInfo: PersonalInfo;
  experiences: ExperienceItem[];
  educations: EducationItem[];
  skills: string[];

  // Actions
  setSelectedCategory: (category: string) => void;
  setSelectedLanguage: (language: string) => void;
  setTemplateColor: (templateId: string, color: string) => void;
  setActiveColor: (color: string) => void;
  setActiveTab: (tab: "info" | "experience" | "education" | "skills") => void;

  initFromTemplate: (templateId: string, customColor?: string) => void;
  updatePersonalInfo: (data: Partial<PersonalInfo>) => void;

  addExperience: () => void;
  updateExperience: (id: string, data: Partial<ExperienceItem>) => void;
  removeExperience: (id: string) => void;

  addEducation: () => void;
  updateEducation: (id: string, data: Partial<EducationItem>) => void;
  removeEducation: (id: string) => void;

  addSkill: (skill: string) => void;
  removeSkill: (index: number) => void;
  resetToTemplate: (templateId: string) => void;
}

const DEFAULT_TEMPLATE = CV_TEMPLATES[0];

/**
 * Debounced storage wrapper: Gom nhiều lần ghi liên tiếp (khi gõ phím) thành 1 lần ghi disk sau delay ms.
 */
function debouncedJSONStorage(getStorage: () => Storage, delay = 500) {
  let timer: number | undefined;
  return {
    getItem: (name: string) => {
      try {
        return getStorage().getItem(name);
      } catch {
        return null;
      }
    },
    setItem: (name: string, value: string) => {
      if (typeof window !== "undefined") {
        window.clearTimeout(timer);
        timer = window.setTimeout(() => {
          try {
            getStorage().setItem(name, value);
          } catch (e) {
            console.error("Lỗi khi lưu CV draft vào storage:", e);
          }
        }, delay);
      }
    },
    removeItem: (name: string) => {
      try {
        getStorage().removeItem(name);
      } catch {
        // Ignore
      }
    },
  };
}

export const useCvDraftStore = create<CvDraftState>()(
  persist(
    (set, get) => ({
      selectedCategory: "all",
      selectedLanguage: "Tiếng Việt",
      templateColors: {},

      templateId: DEFAULT_TEMPLATE.id,
      activeColor: DEFAULT_TEMPLATE.defaultColor,
      activeTab: "info",

      personalInfo: {
        fullName: DEFAULT_TEMPLATE.sampleCandidate.fullName,
        title: DEFAULT_TEMPLATE.sampleCandidate.title,
        email: "ungvien@futurecv.vn",
        phone: "0988 123 456",
        location: "Hà Nội, Việt Nam",
        website: "linkedin.com/in/futurecv-profile",
        avatar: DEFAULT_TEMPLATE.sampleCandidate.avatar,
        summary: DEFAULT_TEMPLATE.sampleCandidate.summary,
      },

      experiences: SAMPLE_EXPERIENCES,
      educations: SAMPLE_EDUCATIONS,
      skills: SAMPLE_SKILLS,

      setSelectedCategory: (selectedCategory) => set({ selectedCategory }),
      setSelectedLanguage: (selectedLanguage) => set({ selectedLanguage }),
      setTemplateColor: (templateId, color) =>
        set((state) => ({
          templateColors: { ...state.templateColors, [templateId]: color },
        })),

      setActiveColor: (activeColor) => set({ activeColor }),
      setActiveTab: (activeTab) => set({ activeTab }),

      initFromTemplate: (templateId, customColor) => {
        const template = CV_TEMPLATES.find((t) => t.id === templateId) ?? CV_TEMPLATES[0];
        const color = customColor || get().templateColors[templateId] || template.defaultColor;

        set((state) => ({
          templateId,
          activeColor: color,
          personalInfo: {
            ...state.personalInfo,
            fullName: state.personalInfo.fullName || template.sampleCandidate.fullName,
            title: state.personalInfo.title || template.sampleCandidate.title,
            avatar: state.personalInfo.avatar || template.sampleCandidate.avatar,
            summary: state.personalInfo.summary || template.sampleCandidate.summary,
          },
        }));
      },

      updatePersonalInfo: (data) =>
        set((state) => ({
          personalInfo: { ...state.personalInfo, ...data },
        })),

      addExperience: () =>
        set((state) => ({
          experiences: [
            ...state.experiences,
            {
              id: `exp-${Date.now()}`,
              role: "Vị trí mới",
              company: "Tên công ty",
              startDate: "01/2024",
              endDate: "Hiện tại",
              description: "• Mô tả thành tích và nhiệm vụ chính tại đây...",
            },
          ],
        })),

      updateExperience: (id, data) =>
        set((state) => ({
          experiences: state.experiences.map((item) =>
            item.id === id ? { ...item, ...data } : item,
          ),
        })),

      removeExperience: (id) =>
        set((state) => ({
          experiences: state.experiences.filter((item) => item.id !== id),
        })),

      addEducation: () =>
        set((state) => ({
          educations: [
            ...state.educations,
            {
              id: `edu-${Date.now()}`,
              degree: "Bằng cấp / Chuyên ngành",
              school: "Tên trường Đại học",
              startDate: "2020",
              endDate: "2024",
              gpa: "GPA: 3.5/4.0",
            },
          ],
        })),

      updateEducation: (id, data) =>
        set((state) => ({
          educations: state.educations.map((item) =>
            item.id === id ? { ...item, ...data } : item,
          ),
        })),

      removeEducation: (id) =>
        set((state) => ({
          educations: state.educations.filter((item) => item.id !== id),
        })),

      addSkill: (skill) => {
        const trimmed = skill.trim();
        if (!trimmed) return;
        set((state) => {
          if (state.skills.includes(trimmed)) return state;
          return { skills: [...state.skills, trimmed] };
        });
      },

      removeSkill: (index) =>
        set((state) => ({
          skills: state.skills.filter((_, i) => i !== index),
        })),

      resetToTemplate: (templateId) => {
        const template = CV_TEMPLATES.find((t) => t.id === templateId) ?? CV_TEMPLATES[0];
        set({
          templateId,
          activeColor: template.defaultColor,
          personalInfo: {
            fullName: template.sampleCandidate.fullName,
            title: template.sampleCandidate.title,
            email: "ungvien@futurecv.vn",
            phone: "0988 123 456",
            location: "Hà Nội, Việt Nam",
            website: "linkedin.com/in/futurecv-profile",
            avatar: template.sampleCandidate.avatar,
            summary: template.sampleCandidate.summary,
          },
          skills: template.sampleCandidate.skills,
        });
      },
    }),
    {
      name: "futurecv-draft-cv",
      storage: createJSONStorage(() => debouncedJSONStorage(() => localStorage, 500)),
      // Chỉ persist domain data — KHÔNG persist activeTab, selectedCategory...
      partialize: (s) => ({
        templateId: s.templateId,
        activeColor: s.activeColor,
        personalInfo: s.personalInfo,
        experiences: s.experiences,
        educations: s.educations,
        skills: s.skills,
      }),
    },
  ),
);
