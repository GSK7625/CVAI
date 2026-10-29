import { useState } from "react";
import { Link } from "react-router";
import { IconMailCog, IconBell, IconBriefcase, IconGift } from "@tabler/icons-react";
import { Switch } from "~/components/ui/Switch";
import { Button } from "~/components/ui/Button";
import { useUIStore } from "~/stores/useUIStore";

export function EmailNotificationSettings() {
  const showToast = useUIStore((s) => s.showToast);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Nhóm 1: Thông báo từ hệ thống
  const [systemNotifications, setSystemNotifications] = useState({
    importantUpdates: true,
    employerProfileViews: true,
    newFeaturesAndTemplates: true,
    otherSystemNotifications: false,
  });

  // Nhóm 2: Thông báo cơ hội việc làm
  const [jobNotifications, setJobNotifications] = useState({
    customAlerts: true,
    matchingJobs: true,
    topCandidateJobs: true,
    interviewInvites: true,
    careerEvents: false,
  });

  // Nhóm 3: Thông báo giới thiệu dịch vụ
  const [serviceNotifications, setServiceNotifications] = useState({
    servicesIntro: false,
    eventsIntro: false,
    partnerPromotions: false,
  });

  const handleSave = () => {
    setIsSubmitting(true);
    setTimeout(() => {
      setIsSubmitting(false);
      showToast("Đã lưu cài đặt thông báo qua email thành công", "success");
    }, 400);
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Outer Shell (Double-Bezel) */}
      <div className="rounded-2xl border border-navy/10 bg-surface/80 p-2 shadow-surface backdrop-blur-sm">
        <div className="rounded-xl border border-border-subtle bg-surface p-6 md:p-8 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]">
          <div className="flex items-center gap-3 border-b border-border-subtle pb-5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-navy/5 text-navy">
              <IconMailCog size={22} stroke={1.6} />
            </div>
            <div>
              <h1 className="text-headline-md font-bold text-navy">Cài đặt thông báo qua email</h1>
              <p className="text-body-sm text-ink-muted">
                Tuỳ chỉnh các loại email bạn muốn nhận từ FutureCV và đối tác
              </p>
            </div>
          </div>

          <div className="space-y-8 pt-6">
            {/* Nhóm 1: Thông báo từ hệ thống */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <IconBell size={18} stroke={1.8} className="text-gold" />
                <h2 className="text-label font-bold uppercase tracking-wider text-navy">
                  Thông báo từ hệ thống
                </h2>
              </div>
              <div className="divide-y divide-border-subtle rounded-xl border border-border-subtle bg-surface-low/30 px-4">
                <div className="flex items-center justify-between py-3.5">
                  <span className="text-label font-medium text-navy">Cập nhật quan trọng từ hệ thống</span>
                  <Switch
                    checked={systemNotifications.importantUpdates}
                    onChange={(checked) =>
                      setSystemNotifications((prev) => ({ ...prev, importantUpdates: checked }))
                    }
                    ariaLabel="Cập nhật quan trọng từ hệ thống"
                  />
                </div>
                <div className="flex items-center justify-between py-3.5">
                  <span className="text-label font-medium text-navy">Thông báo nhà tuyển dụng đã xem CV</span>
                  <Switch
                    checked={systemNotifications.employerProfileViews}
                    onChange={(checked) =>
                      setSystemNotifications((prev) => ({ ...prev, employerProfileViews: checked }))
                    }
                    ariaLabel="Thông báo nhà tuyển dụng đã xem CV"
                  />
                </div>
                <div className="flex items-center justify-between py-3.5">
                  <span className="text-label font-medium text-navy">Thông báo tính năng và mẫu CV mới</span>
                  <Switch
                    checked={systemNotifications.newFeaturesAndTemplates}
                    onChange={(checked) =>
                      setSystemNotifications((prev) => ({ ...prev, newFeaturesAndTemplates: checked }))
                    }
                    ariaLabel="Thông báo tính năng và mẫu CV mới"
                  />
                </div>
                <div className="flex items-center justify-between py-3.5">
                  <span className="text-label font-medium text-navy">Thông báo khác từ hệ thống</span>
                  <Switch
                    checked={systemNotifications.otherSystemNotifications}
                    onChange={(checked) =>
                      setSystemNotifications((prev) => ({ ...prev, otherSystemNotifications: checked }))
                    }
                    ariaLabel="Thông báo khác từ hệ thống"
                  />
                </div>
              </div>
            </div>

            {/* Nhóm 2: Thông báo cơ hội việc làm */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <IconBriefcase size={18} stroke={1.8} className="text-gold" />
                <h2 className="text-label font-bold uppercase tracking-wider text-navy">
                  Thông báo cơ hội việc làm
                </h2>
              </div>
              <div className="divide-y divide-border-subtle rounded-xl border border-border-subtle bg-surface-low/30 px-4">
                <div className="flex items-center justify-between py-3.5">
                  <div className="flex flex-wrap items-center gap-1.5 pr-2">
                    <span className="text-label font-medium text-navy">
                      Thông báo việc làm theo thiết lập
                    </span>
                    <Link
                      to="/candidate/job-alerts"
                      className="text-label-sm font-semibold text-gold hover:underline"
                    >
                      (Xem danh sách thiết lập)
                    </Link>
                  </div>
                  <Switch
                    checked={jobNotifications.customAlerts}
                    onChange={(checked) =>
                      setJobNotifications((prev) => ({ ...prev, customAlerts: checked }))
                    }
                    ariaLabel="Thông báo việc làm theo thiết lập"
                  />
                </div>
                <div className="flex items-center justify-between py-3.5">
                  <span className="text-label font-medium text-navy">
                    Thông báo việc làm phù hợp từ hệ thống
                  </span>
                  <Switch
                    checked={jobNotifications.matchingJobs}
                    onChange={(checked) =>
                      setJobNotifications((prev) => ({ ...prev, matchingJobs: checked }))
                    }
                    ariaLabel="Thông báo việc làm phù hợp từ hệ thống"
                  />
                </div>
                <div className="flex items-center justify-between py-3.5">
                  <span className="text-label font-medium text-navy">
                    Thông báo việc làm bạn là ứng viên hàng đầu
                  </span>
                  <Switch
                    checked={jobNotifications.topCandidateJobs}
                    onChange={(checked) =>
                      setJobNotifications((prev) => ({ ...prev, topCandidateJobs: checked }))
                    }
                    ariaLabel="Thông báo việc làm bạn là ứng viên hàng đầu"
                  />
                </div>
                <div className="flex items-center justify-between py-3.5">
                  <span className="text-label font-medium text-navy">
                    Thông báo nhà tuyển dụng gửi mời lời phỏng vấn / ứng tuyển
                  </span>
                  <Switch
                    checked={jobNotifications.interviewInvites}
                    onChange={(checked) =>
                      setJobNotifications((prev) => ({ ...prev, interviewInvites: checked }))
                    }
                    ariaLabel="Thông báo nhà tuyển dụng mời phỏng vấn"
                  />
                </div>
                <div className="flex items-center justify-between py-3.5">
                  <span className="text-label font-medium text-navy">
                    Thông tin liên quan đến việc làm, sự kiện nghề nghiệp
                  </span>
                  <Switch
                    checked={jobNotifications.careerEvents}
                    onChange={(checked) =>
                      setJobNotifications((prev) => ({ ...prev, careerEvents: checked }))
                    }
                    ariaLabel="Thông tin sự kiện nghề nghiệp"
                  />
                </div>
              </div>
            </div>

            {/* Nhóm 3: Thông báo giới thiệu dịch vụ */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <IconGift size={18} stroke={1.8} className="text-gold" />
                <h2 className="text-label font-bold uppercase tracking-wider text-navy">
                  Thông báo giới thiệu dịch vụ
                </h2>
              </div>
              <div className="divide-y divide-border-subtle rounded-xl border border-border-subtle bg-surface-low/30 px-4">
                <div className="flex items-center justify-between py-3.5">
                  <span className="text-label font-medium text-navy">Giới thiệu các dịch vụ</span>
                  <Switch
                    checked={serviceNotifications.servicesIntro}
                    onChange={(checked) =>
                      setServiceNotifications((prev) => ({ ...prev, servicesIntro: checked }))
                    }
                    ariaLabel="Giới thiệu các dịch vụ"
                  />
                </div>
                <div className="flex items-center justify-between py-3.5">
                  <span className="text-label font-medium text-navy">Giới thiệu chương trình, sự kiện</span>
                  <Switch
                    checked={serviceNotifications.eventsIntro}
                    onChange={(checked) =>
                      setServiceNotifications((prev) => ({ ...prev, eventsIntro: checked }))
                    }
                    ariaLabel="Giới thiệu chương trình, sự kiện"
                  />
                </div>
                <div className="flex items-center justify-between py-3.5">
                  <span className="text-label font-medium text-navy">
                    Quà tặng / Mã giảm giá từ các đối tác
                  </span>
                  <Switch
                    checked={serviceNotifications.partnerPromotions}
                    onChange={(checked) =>
                      setServiceNotifications((prev) => ({ ...prev, partnerPromotions: checked }))
                    }
                    ariaLabel="Quà tặng / Mã giảm giá từ các đối tác"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="mt-8 pt-4 border-t border-border-subtle">
            <Button
              type="button"
              disabled={isSubmitting}
              onClick={handleSave}
              className="min-w-[120px] rounded-lg bg-navy px-6 py-2.5 text-label font-semibold text-white shadow-sm transition-all hover:bg-navy-secondary active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? "Đang lưu..." : "Lưu cài đặt"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
