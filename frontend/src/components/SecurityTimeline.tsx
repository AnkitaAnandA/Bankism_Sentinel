import { memo, useState } from "react";
import type { Event } from "../services/api";
import { Badge, CodeBlock, Dialog, EmptyState, KeyValue, Table } from "../ui";
import { humanize, shortTime } from "../ui/format";
export default memo(function SecurityTimeline({ events }: { events: Event[] }) {
  const [selected, setSelected] = useState<Event | null>(null);
  return (
    <>
      {events.length ? (
        <Table label="Security events — scroll to inspect all columns">
          <thead>
            <tr>
              <th>Time</th>
              <th>Decision</th>
              <th>Threat category</th>
              <th>Redacted evidence</th>
              <th>Inspect</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event) => (
              <tr className="event-table-row" key={event.request_id}>
                <td>{shortTime(event.timestamp)}</td>
                <td>
                  <Badge tone={event.verdict}>{event.verdict}</Badge>
                </td>
                <td>
                  {event.category === "NONE"
                    ? "No threat"
                    : humanize(event.category)}
                </td>
                <td className="event-evidence">
                  <span>{event.evidence}</span>
                </td>
                <td>
                  <button
                    className="event-link"
                    onClick={() => setSelected(event)}
                    aria-label={`Inspect event ${event.request_id.slice(0, 8)}`}
                  >
                    {event.request_id.slice(0, 8)}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      ) : (
        <EmptyState
          title="No matching events"
          description="Try a different filter, or send a banking request to populate the audit trail."
        />
      )}
      <Dialog
        open={selected !== null}
        onClose={() => setSelected(null)}
        title="Security event"
      >
        {selected && (
          <>
            <KeyValue
              rows={[
                [
                  "Decision",
                  <Badge tone={selected.verdict}>{selected.verdict}</Badge>,
                ],
                ["Risk", humanize(selected.risk)],
                ["Category", humanize(selected.category)],
                [
                  "Request ID",
                  <span className="mono break">{selected.request_id}</span>,
                ],
                ["Time", new Date(selected.timestamp * 1000).toLocaleString()],
              ]}
            />
            <p className="small" style={{ marginTop: 16 }}>
              {selected.evidence}
            </p>
            <CodeBlock value={selected} />
          </>
        )}
      </Dialog>
    </>
  );
});
