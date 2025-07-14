export default function SearchV2Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="h-[calc(100vh-4rem)] -m-8 overflow-hidden">
      {children}
    </div>
  );
}