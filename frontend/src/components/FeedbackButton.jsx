import { Button } from "@/components/ui/button";

export function FeedbackButton() {
  return (
    <Button
      type="button"
      title="Give feedback"
      variant="link"
      size="sm"
      className="rotate-270 !rounded-tl-[10px] !rounded-tr-[10px] hover:no-underline"
      onClick={() =>
        window.open(
          "https://forms.office.com/Pages/ResponsePage.aspx?id=t-dzXeGzAE2zAwVhQLKjtCrb7J-ALhtKgobfFu7XlK1UQlFDTEgxMVFUUE8xSlVPVExBRDJLNDIzRC4u",
          "_blank"
        )
      }>
      Give feedback
    </Button>
  );
}
