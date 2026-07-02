export default function SystemMessage({ index, value }) {
  return (
    <>
      <div
        key={index}
        className="flex w-full items-start justify-start gap-2 pr-[5%]">
        <div className="flex w-full flex-col items-start">
          <Response className="w-full rounded-lg border border-gray-200 bg-gray-50 p-2 text-sm wrap-break-word">
            {value}
          </Response>
        </div>
      </div>
    </>
  );
}
