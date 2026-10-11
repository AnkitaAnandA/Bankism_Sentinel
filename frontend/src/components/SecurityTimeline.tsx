import { memo } from "react";
import type { Event } from "../services/api";
export default memo(function SecurityTimeline({ events }: { events: Event[] }) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Verdict</th>
            <th>Threat category</th>
            <th>Evidence</th>
            <th>Request ID</th>
          </tr>
        </thead>
        <tbody>
          {events.map((e) => (
            <tr key={e.request_id}>
              <td>{new Date(e.timestamp * 1000).toLocaleTimeString()}</td>
              <td>
                <span className={"badge " + e.verdict.toLowerCase()}>
                  {e.verdict}
                </span>
              </td>
              <td>{e.category.replaceAll("_", " ")}</td>
              <td>{e.evidence}</td>
              <td className="mono">{e.request_id.slice(0, 8)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {!events.length && (
        <p className="empty">
          No audit events yet. Send a banking request to create one.
        </p>
      )}
    </div>
  );
});
