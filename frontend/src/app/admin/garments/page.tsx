"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import type {
  KeyboardEvent as ReactKeyboardEvent,
  MouseEvent as ReactMouseEvent,
} from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import {
  AlertCircle,
  Eye,
  MoreHorizontal,
  PackagePlus,
  RefreshCw,
  Search,
  Trash2,
} from "lucide-react";
import { GarmentImage } from "@/components/admin/GarmentImage";
import {
  deleteGarment,
  listGarments,
  retryGarmentIngestion,
  type Garment,
} from "@/lib/admin/garments";

type StatusFilter = "all" | "ready" | "processing" | "failed";

const filters: { value: StatusFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "ready", label: "Ready" },
  { value: "processing", label: "Processing" },
  { value: "failed", label: "Failed" },
];

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function getStatusLabel(status: string) {
  const normalizedStatus = status.toLowerCase();

  if (normalizedStatus === "ready") return "Ready";
  if (normalizedStatus === "processing") return "Processing";
  if (normalizedStatus === "failed") return "Failed";
  if (normalizedStatus === "draft") return "Draft";
  if (normalizedStatus === "pending") return "Pending";

  return status || "Pending";
}

function getStatusClasses(status: string) {
  const normalizedStatus = status.toLowerCase();

  if (normalizedStatus === "ready") {
    return "bg-emerald-50 text-emerald-700 ring-emerald-200/80";
  }

  if (normalizedStatus === "processing") {
    return "bg-amber-50 text-amber-700 ring-amber-200/80";
  }

  if (normalizedStatus === "failed") {
    return "bg-rose-50 text-rose-700 ring-rose-200/80";
  }

  return "bg-slate-100 text-slate-600 ring-slate-200/80";
}

function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1 ${getStatusClasses(status)}`}
    >
      {getStatusLabel(status)}
    </span>
  );
}

function getGarmentHref(garmentId: string) {
  return `/admin/garments/${garmentId}`;
}

function isInteractiveTarget(target: EventTarget | null) {
  if (!(target instanceof Element)) {
    return false;
  }

  return Boolean(
    target.closest(
      'a, button, input, select, textarea, [role="menu"], [data-row-interactive="true"]'
    )
  );
}

type GarmentActionsMenuProps = {
  garment: Garment;
  isOpen: boolean;
  isDeleting: boolean;
  isRebuilding: boolean;
  onToggle: () => void;
  onClose: () => void;
  onView: () => void;
  onDelete: () => void;
  onRebuild: () => void;
};

function GarmentActionsMenu({
  garment,
  isOpen,
  isDeleting,
  isRebuilding,
  onToggle,
  onClose,
  onView,
  onDelete,
  onRebuild,
}: GarmentActionsMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);
  const menuId = `garment-actions-${garment.id}`;

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    function handlePointerDown(event: PointerEvent) {
      if (menuRef.current?.contains(event.target as Node)) {
        return;
      }

      onClose();
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key !== "Escape") {
        return;
      }

      event.preventDefault();
      onClose();
    }

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  return (
    <div
      ref={menuRef}
      data-row-interactive="true"
      className="relative inline-flex justify-end"
      onClick={(event) => event.stopPropagation()}
      onKeyDown={(event) => event.stopPropagation()}
    >
      <button
        type="button"
        onClick={onToggle}
        aria-label={`Open actions for ${garment.name}`}
        aria-controls={menuId}
        aria-expanded={isOpen}
        aria-haspopup="menu"
        className="inline-flex h-9 w-9 cursor-pointer items-center justify-center rounded-full border border-tavaura-ink/10 bg-white/90 text-tavaura-ink shadow-sm transition hover:bg-tavaura-ink/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tavaura-ink/20"
      >
        <MoreHorizontal size={18} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            id={menuId}
            role="menu"
            aria-label={`Actions for ${garment.name}`}
            className="absolute right-0 top-11 z-40 w-52 overflow-hidden rounded-2xl border border-white/70 bg-white/85 py-2 text-sm font-medium text-tavaura-ink shadow-2xl shadow-tavaura-ink/15 ring-1 ring-tavaura-ink/5 backdrop-blur-xl"
            initial={{ opacity: 0, y: -4, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.98 }}
            transition={{ duration: 0.16, ease: "easeOut" }}
          >
            <button
              type="button"
              role="menuitem"
              onClick={onView}
              className="flex w-full cursor-pointer items-center gap-2 px-4 py-2.5 text-left transition hover:bg-tavaura-bg focus-visible:bg-tavaura-bg focus-visible:outline-none"
            >
              <Eye size={15} />
              View Details
            </button>
            <button
              type="button"
              role="menuitem"
              disabled={isRebuilding}
              onClick={onRebuild}
              className="flex w-full cursor-pointer items-center gap-2 px-4 py-2.5 text-left transition hover:bg-tavaura-bg focus-visible:bg-tavaura-bg focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-60"
            >
              <RefreshCw size={15} />
              {isRebuilding ? "Queueing..." : "Rebuild Asset"}
            </button>
            <div className="my-1 h-px bg-tavaura-ink/8" />
            <button
              type="button"
              role="menuitem"
              disabled={isDeleting}
              onClick={onDelete}
              className="flex w-full cursor-pointer items-center gap-2 px-4 py-2.5 text-left text-rose-700 transition hover:bg-rose-50 focus-visible:bg-rose-50 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Trash2 size={15} />
              {isDeleting ? "Deleting..." : "Delete"}
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function AdminGarmentsPage() {
  const router = useRouter();
  const [garments, setGarments] = useState<Garment[]>([]);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<StatusFilter>("all");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [rebuildingId, setRebuildingId] = useState<string | null>(null);
  const [openActionMenuId, setOpenActionMenuId] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadGarments() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await listGarments();
        if (isMounted) {
          setGarments(data);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Unable to load garments.");
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadGarments();

    return () => {
      isMounted = false;
    };
  }, []);

  const filteredGarments = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return garments.filter((garment) => {
      const matchesFilter = filter === "all" || garment.status === filter;
      const matchesQuery =
        !normalizedQuery ||
        garment.name.toLowerCase().includes(normalizedQuery) ||
        garment.externalProductId.toLowerCase().includes(normalizedQuery) ||
        garment.category.toLowerCase().includes(normalizedQuery) ||
        garment.layer.toLowerCase().includes(normalizedQuery);

      return matchesFilter && matchesQuery;
    });
  }, [filter, garments, query]);

  const handleDelete = async (garment: Garment) => {
    setOpenActionMenuId(null);

    const confirmed = window.confirm("Delete this garment?");
    if (!confirmed) {
      return;
    }

    setDeletingId(garment.id);
    setError(null);
    setNotice(null);
    try {
      await deleteGarment(garment.id);
      setGarments((current) => current.filter((item) => item.id !== garment.id));
      setNotice(`${garment.name} was removed from the active catalog.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete garment.");
    } finally {
      setDeletingId(null);
    }
  };

  const handleRebuildAsset = async (garment: Garment) => {
    setOpenActionMenuId(null);
    setRebuildingId(garment.id);
    setError(null);
    setNotice(null);

    try {
      await retryGarmentIngestion(garment.id);
      setGarments((current) =>
        current.map((item) =>
          item.id === garment.id
            ? {
                ...item,
                status: "processing",
                latestIngestionStatus: "pending",
                latestIngestionErrorMessage: null,
              }
            : item
        )
      );
      setNotice(`${garment.name} asset rebuild was queued.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to rebuild asset.");
    } finally {
      setRebuildingId(null);
    }
  };

  const openGarmentDetail = (garment: Garment) => {
    router.push(getGarmentHref(garment.id));
  };

  const handleGarmentClick = (
    event: ReactMouseEvent<HTMLElement>,
    garment: Garment
  ) => {
    if (isInteractiveTarget(event.target)) {
      return;
    }

    openGarmentDetail(garment);
  };

  const handleGarmentKeyDown = (
    event: ReactKeyboardEvent<HTMLElement>,
    garment: Garment
  ) => {
    if (event.target !== event.currentTarget) {
      return;
    }

    if (event.key !== "Enter" && event.key !== " ") {
      return;
    }

    event.preventDefault();
    openGarmentDetail(garment);
  };

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-4 rounded-[2rem] border border-white/70 bg-white/80 p-5 shadow-tavaura backdrop-blur-xl sm:p-6 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-tavaura-ink/60">
            Catalog
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-tavaura-ink">
            Garments
          </h1>
          <p className="mt-2 text-sm text-tavaura-ink/70">
            Manage your catalog assets.
          </p>
        </div>
        <Link
          href="/admin/garments/new"
          className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-full bg-tavaura-ink px-5 py-3 text-sm font-semibold text-white shadow-tavaura transition hover:bg-tavaura-ink/90"
        >
          <PackagePlus size={17} />
          Add Garment
        </Link>
      </section>

      <section className="rounded-3xl border border-white/70 bg-white/80 p-4 shadow-tavaura-sm backdrop-blur sm:p-5">
        <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_220px]">
          <label className="relative block">
            <Search
              size={17}
              className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-tavaura-ink/45"
            />
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search by name or Product ID"
              className="w-full rounded-2xl border border-tavaura-ink/10 bg-white px-11 py-3 text-sm text-tavaura-ink shadow-sm outline-none transition focus:border-tavaura-ink focus:ring-2 focus:ring-tavaura-ink/10"
            />
          </label>
          <select
            value={filter}
            onChange={(event) => setFilter(event.target.value as StatusFilter)}
            className="cursor-pointer rounded-2xl border border-tavaura-ink/10 bg-white px-4 py-3 text-sm font-medium text-tavaura-ink shadow-sm outline-none transition focus:border-tavaura-ink focus:ring-2 focus:ring-tavaura-ink/10"
          >
            {filters.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </div>
      </section>

      {error && (
        <div className="flex items-start gap-3 rounded-3xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">
          <AlertCircle size={18} className="mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {notice && (
        <div className="rounded-3xl border border-emerald-200 bg-emerald-50 px-5 py-4 text-sm font-medium text-emerald-700">
          {notice}
        </div>
      )}

      <section className="rounded-[2rem] border border-white/70 bg-white/80 p-4 shadow-tavaura-sm backdrop-blur sm:p-5">
        {isLoading ? (
          <div className="py-14 text-center text-sm font-medium text-tavaura-ink/65">
            Loading garments...
          </div>
        ) : garments.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-tavaura-ink/15 bg-tavaura-bg/70 px-5 py-12 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-tavaura-ink shadow-tavaura-sm">
              <PackagePlus size={22} />
            </div>
            <p className="text-sm font-semibold text-tavaura-ink">No garments yet.</p>
            <p className="mx-auto mt-2 max-w-md text-xs leading-5 text-tavaura-ink/60">
              Upload your first catalog item.
            </p>
            <Link
              href="/admin/garments/new"
              className="mt-5 inline-flex cursor-pointer items-center justify-center gap-2 rounded-full bg-tavaura-ink px-5 py-3 text-sm font-semibold text-white shadow-tavaura transition hover:bg-tavaura-ink/90"
            >
              <PackagePlus size={17} />
              Add Garment
            </Link>
          </div>
        ) : filteredGarments.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-tavaura-ink/15 bg-tavaura-bg/70 px-5 py-12 text-center">
            <p className="text-sm font-semibold text-tavaura-ink">No matching garments</p>
            <p className="mt-2 text-xs text-tavaura-ink/60">
              Adjust your search or filters to find catalog assets.
            </p>
          </div>
        ) : (
          <>
            <div className="relative hidden rounded-3xl border border-tavaura-ink/8 bg-white lg:block">
              <table className="w-full table-fixed text-left text-sm">
                <colgroup>
                  <col className="w-[38%]" />
                  <col className="w-[15%]" />
                  <col className="w-[13%]" />
                  <col className="w-[13%]" />
                  <col className="w-[14%]" />
                  <col className="w-[7%]" />
                </colgroup>
                <thead className="bg-tavaura-bg/80 text-xs font-semibold uppercase tracking-[0.14em] text-tavaura-ink/55">
                  <tr>
                    <th className="rounded-tl-3xl px-4 py-3">Garment</th>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3">Layer</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Created</th>
                    <th className="rounded-tr-3xl px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-tavaura-ink/8">
                  {filteredGarments.map((garment) => (
                    <tr
                      key={garment.id}
                      role="link"
                      tabIndex={0}
                      aria-label={`Open details for ${garment.name}`}
                      onClick={(event) => handleGarmentClick(event, garment)}
                      onKeyDown={(event) => handleGarmentKeyDown(event, garment)}
                      className="cursor-pointer transition hover:bg-tavaura-bg/50 focus-visible:bg-tavaura-bg/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-tavaura-ink/15"
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <GarmentImage
                            name={garment.name}
                            imageUrl={garment.sourceImageUrl}
                            className="h-14 w-14"
                          />
                          <div className="min-w-0">
                            <Link
                              href={getGarmentHref(garment.id)}
                              onClick={(event) => event.stopPropagation()}
                              className="block cursor-pointer truncate font-semibold text-tavaura-ink transition hover:text-tavaura-cocoa focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tavaura-ink/15"
                            >
                              {garment.name}
                            </Link>
                            <p className="mt-1 truncate text-xs text-tavaura-ink/55">
                              Product ID: {garment.externalProductId}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="truncate px-4 py-3 text-tavaura-ink/75">{garment.category}</td>
                      <td className="truncate px-4 py-3 text-tavaura-ink/75">{garment.layer}</td>
                      <td className="px-4 py-3">
                        <StatusBadge status={garment.status} />
                      </td>
                      <td className="truncate px-4 py-3 text-tavaura-ink/65">
                        {formatDate(garment.createdAt)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <GarmentActionsMenu
                          garment={garment}
                          isOpen={openActionMenuId === garment.id}
                          isDeleting={deletingId === garment.id}
                          isRebuilding={rebuildingId === garment.id}
                          onToggle={() =>
                            setOpenActionMenuId((current) =>
                              current === garment.id ? null : garment.id
                            )
                          }
                          onClose={() => setOpenActionMenuId(null)}
                          onView={() => {
                            setOpenActionMenuId(null);
                            openGarmentDetail(garment);
                          }}
                          onRebuild={() => void handleRebuildAsset(garment)}
                          onDelete={() => void handleDelete(garment)}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="space-y-3 lg:hidden">
              {filteredGarments.map((garment) => (
                <article
                  key={garment.id}
                  role="link"
                  tabIndex={0}
                  aria-label={`Open details for ${garment.name}`}
                  onClick={(event) => handleGarmentClick(event, garment)}
                  onKeyDown={(event) => handleGarmentKeyDown(event, garment)}
                  className="relative cursor-pointer rounded-3xl border border-tavaura-ink/8 bg-white/95 p-4 shadow-tavaura-sm transition hover:bg-white hover:shadow-tavaura focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tavaura-ink/15"
                >
                  <div className="flex gap-4">
                    <GarmentImage
                      name={garment.name}
                      imageUrl={garment.sourceImageUrl}
                      className="h-20 w-20 rounded-2xl sm:h-24 sm:w-24"
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <Link
                            href={getGarmentHref(garment.id)}
                            onClick={(event) => event.stopPropagation()}
                            className="block cursor-pointer truncate font-semibold text-tavaura-ink transition hover:text-tavaura-cocoa focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-tavaura-ink/15"
                          >
                            {garment.name}
                          </Link>
                          <p className="mt-1 truncate text-xs text-tavaura-ink/55">
                            Product ID: {garment.externalProductId}
                          </p>
                        </div>
                        <GarmentActionsMenu
                          garment={garment}
                          isOpen={openActionMenuId === garment.id}
                          isDeleting={deletingId === garment.id}
                          isRebuilding={rebuildingId === garment.id}
                          onToggle={() =>
                            setOpenActionMenuId((current) =>
                              current === garment.id ? null : garment.id
                            )
                          }
                          onClose={() => setOpenActionMenuId(null)}
                          onView={() => {
                            setOpenActionMenuId(null);
                            openGarmentDetail(garment);
                          }}
                          onRebuild={() => void handleRebuildAsset(garment)}
                          onDelete={() => void handleDelete(garment)}
                        />
                      </div>
                      <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-2 text-xs text-tavaura-ink/70">
                        <span>
                          {garment.category} {"\u2022"} {garment.layer}
                        </span>
                        <span>
                          <StatusBadge status={garment.status} />
                        </span>
                      </div>
                      <div className="mt-3 text-xs text-tavaura-ink/55">
                        Created {formatDate(garment.createdAt)}
                      </div>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </>
        )}
      </section>
    </div>
  );
}
