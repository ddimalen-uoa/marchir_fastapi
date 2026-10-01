import { useEffect, useId, useRef, useState } from "react";
import type { ReactNode } from "react";
import * as Popover from "@radix-ui/react-popover";
import { Info } from "lucide-react";

export function LoginHelpPopover({ title, label, children, text }: {
  title: string;
  label: string;
  children: ReactNode;
  text?: string;
}) {
  const [open, setOpen] = useState(false);
  const bodyId = useId();
  const triggerRef = useRef<HTMLButtonElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  function cancelClose() {
    if (closeTimer.current) clearTimeout(closeTimer.current);
    closeTimer.current = null;
  }

  function show() {
    cancelClose();
    setOpen(true);
  }

  function scheduleClose() {
    cancelClose();
    closeTimer.current = setTimeout(() => setOpen(false), 180);
  }

  function handleBlur(target: EventTarget | null) {
    if (target instanceof Node && (triggerRef.current?.contains(target) || contentRef.current?.contains(target))) return;
    scheduleClose();
  }

  useEffect(() => () => { if (closeTimer.current) clearTimeout(closeTimer.current); }, []);

  return (
    <Popover.Root open={open} onOpenChange={(nextOpen) => { cancelClose(); setOpen(nextOpen); }}>
      <Popover.Trigger asChild>
        <button
          ref={triggerRef}
          type="button"
          aria-label={label}
          aria-describedby={open ? bodyId : undefined}
          onMouseEnter={show}
          onMouseLeave={scheduleClose}
          onFocus={(event) => { if (event.currentTarget.matches(":focus-visible")) show(); }}
          onBlur={(event) => handleBlur(event.relatedTarget)}
          onClick={(event) => { event.preventDefault(); show(); }}
          className={`inline-flex shrink-0 items-center justify-center gap-1.5 rounded-md text-white/70 transition hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-300 ${text ? "px-2 py-1 text-xs underline decoration-white/40 underline-offset-4" : "h-7 w-7"}`}
        >
          <Info className="h-4 w-4 shrink-0" aria-hidden="true" />
          {text}
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          ref={contentRef}
          side={text ? "bottom" : "top"}
          sideOffset={10}
          collisionPadding={16}
          aria-label={title}
          aria-describedby={bodyId}
          onMouseEnter={cancelClose}
          onMouseLeave={scheduleClose}
          onFocusCapture={cancelClose}
          onBlurCapture={(event) => handleBlur(event.relatedTarget)}
          onOpenAutoFocus={(event) => event.preventDefault()}
          onCloseAutoFocus={(event) => event.preventDefault()}
          className="z-50 max-h-[calc(100dvh_-_2rem)] w-80 max-w-[calc(100vw_-_2rem)] overflow-y-auto rounded-lg border border-gray-200 bg-white text-left text-sm text-gray-600 shadow-lg"
        >
          <div className="rounded-t-lg border-b border-gray-200 bg-gray-100 px-3 py-2">
            <h2 className="text-sm font-semibold text-gray-900">{title}</h2>
          </div>
          <div id={bodyId} className="space-y-3 break-words px-3 py-3 leading-5">{children}</div>
          <Popover.Arrow className="fill-white" width={12} height={6} />
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
