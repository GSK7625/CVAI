/**
 * Re-export useCvDraftStore để đảm bảo tính tương thích ngược cho toàn bộ codebase.
 */
export {
  useCvDraftStore as useCvStore,
  type ExperienceItem,
  type EducationItem,
  type PersonalInfo,
  type CvPersonalInfo,
  type CvExperience,
  type CvEducation,
  type CvDraftState as CvState,
} from "~/features/candidate/stores/useCvDraftStore";
