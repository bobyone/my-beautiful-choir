// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import { useRef, useState } from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Modal from "react-bootstrap/Modal";
import { useTranslation } from "react-i18next";

import { parseDeletionInfo } from "../deletion/deletionInfo";
import { type CallTool, resultData } from "../viewData";
import { readScoreFile } from "./readScoreFile";
import { ScoreTable } from "./ScoreTable";
import { WorkDetails } from "./WorkDetails";
import { parseScore, type ScoreInfo, type WorkResult } from "./workInfo";

type Action = "upload" | "open" | "delete";
type Outcome = { action: Action; state: "waiting" | "done" | "failed" };
type Deletion = {
  id: string;
  label: string;
  tool: "delete_score_from_view" | "delete_work_from_view";
};

export function WorkPanel({
  data,
  callTool,
  onBack,
}: {
  data: WorkResult;
  callTool: CallTool;
  onBack?: () => void;
}) {
  const { t } = useTranslation();
  const [scores, setScores] = useState(data.scores);
  const [removed, setRemoved] = useState(false);
  const [deletion, setDeletion] = useState<Deletion | null>(null);
  const [outcome, setOutcome] = useState<Outcome>();
  const fileInput = useRef<HTMLInputElement>(null);
  const busy = outcome?.state === "waiting";

  async function perform(action: Action, task: () => Promise<void>): Promise<void> {
    setOutcome({ action, state: "waiting" });
    try {
      await task();
      setOutcome({ action, state: "done" });
    } catch {
      setOutcome({ action, state: "failed" });
    }
  }

  const upload = (file: File) => {
    void perform("upload", async () => {
      const content = await readScoreFile(file);
      const reply = await callTool("upload_score", {
        work_id: data.work.id,
        file_name: file.name,
        content,
      });
      const score = parseScore(resultData(reply)?.["score"]);
      if (!score) throw new Error("The uploaded score was not returned.");
      setScores((previous) => [...previous, score]);
    });
  };

  const openScore = (score: ScoreInfo) => {
    void perform("open", async () => {
      const reply = await callTool("open_score", { score_id: score.id });
      if (reply.isError === true) throw new Error("The score could not be opened.");
    });
  };

  const confirmDeletion = () => {
    if (deletion === null) return;
    setDeletion(null);
    void perform("delete", async () => {
      const reply = await callTool(deletion.tool, { target_id: deletion.id });
      if (parseDeletionInfo(reply)?.status !== "deleted") throw new Error("The deletion failed.");
      if (deletion.tool === "delete_work_from_view") setRemoved(true);
      else setScores((previous) => previous.filter((score) => score.id !== deletion.id));
    });
  };

  return (
    <section className="p-3" aria-labelledby="work-heading">
      {onBack !== undefined && (
        <Button variant="outline-secondary" className="mb-3" disabled={busy} onClick={onBack}>
          {t("work.back")}
        </Button>
      )}
      <h1 id="work-heading" className="h4">
        {data.work.title}
      </h1>
      {outcome && <WorkFeedback outcome={outcome} />}
      {!removed && (
        <>
          <WorkDetails data={data} />
          <h2 className="h5">{t("deletion.scores")}</h2>
          <ScoreTable
            scores={scores}
            busy={busy}
            onOpen={openScore}
            onDelete={(score) => {
              setDeletion({ id: score.id, label: score.label, tool: "delete_score_from_view" });
            }}
          />
          <div className="d-flex flex-wrap gap-2">
            <input
              type="file"
              ref={fileInput}
              hidden
              accept=".pdf,.musicxml,.mxl,.mscz"
              onChange={(event) => {
                const file = event.currentTarget.files?.[0];
                event.currentTarget.value = "";
                if (file) upload(file);
              }}
            />
            <Button disabled={busy} onClick={() => fileInput.current?.click()}>
              {t("work.addScore")}
            </Button>
            <Button
              variant="outline-danger"
              disabled={busy}
              onClick={() => {
                setDeletion({
                  id: data.work.id,
                  label: data.work.title,
                  tool: "delete_work_from_view",
                });
              }}
            >
              {t("work.deleteWork")}
            </Button>
          </div>
        </>
      )}
      <Modal
        show={deletion !== null}
        onHide={() => {
          setDeletion(null);
        }}
        aria-labelledby="confirm-work-deletion"
      >
        <Modal.Header>
          <Modal.Title id="confirm-work-deletion">{t("glossary.deletion")}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p className="fw-semibold">{deletion?.label}</p>
          {deletion?.tool === "delete_work_from_view" && <p>{t("work.deleteWithScores")}</p>}
          <p>{t("deletion.warning")}</p>
        </Modal.Body>
        <Modal.Footer>
          <Button
            variant="secondary"
            autoFocus
            onClick={() => {
              setDeletion(null);
            }}
          >
            {t("deletion.cancel")}
          </Button>
          <Button variant="danger" onClick={confirmDeletion}>
            {t("deletion.delete")}
          </Button>
        </Modal.Footer>
      </Modal>
    </section>
  );
}

function WorkFeedback({ outcome }: { outcome: Outcome }) {
  const { t } = useTranslation();
  if (outcome.state === "waiting") {
    return (
      <p role="status">
        {outcome.action === "delete" ? t("deletion.deleting") : t("view.loading")}
      </p>
    );
  }
  if (outcome.state === "failed") {
    const message =
      outcome.action === "upload"
        ? t("work.uploadError")
        : outcome.action === "open"
          ? t("work.openError")
          : t("deletion.failed");
    return <Alert variant="danger">{message}</Alert>;
  }
  const message =
    outcome.action === "upload"
      ? t("work.uploaded")
      : outcome.action === "open"
        ? t("work.opened")
        : t("deletion.done");
  return <Alert variant="success">{message}</Alert>;
}
