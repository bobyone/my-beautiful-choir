// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-FileContributor: bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import { useRef, useState } from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Modal from "react-bootstrap/Modal";
import { useTranslation } from "react-i18next";

import type { DownloadFile } from "../../host/useHost";
import { type DeletionInfo, parseDeletionInfo } from "../deletion/deletionInfo";
import { CONFIRM_TOOL } from "../deletion/DeletionApp";
import { DeletionSummaryView } from "../deletion/DeletionView";
import { type CallTool, resultData } from "../viewData";
import { requestTranscription, type TranscriptionOutcome } from "./requestTranscription";
import { readScoreFile } from "./readScoreFile";
import { ScoreTable } from "./ScoreTable";
import { WorkDetails } from "./WorkDetails";
import { parseScore, type ScoreInfo, scoreFile, type WorkResult } from "./workInfo";

type Action = "upload" | "open" | "download" | "prepare-delete" | "delete";
type Outcome = { action: Action; state: "waiting" | "done" | "cancelled" | "failed" };
type Deletion = {
  id: string;
  preview: Extract<DeletionInfo, { status: "pending" }>;
  refreshed: boolean;
};

export function WorkPanel({
  data,
  callTool,
  downloadFile,
  onBack,
}: {
  data: WorkResult;
  callTool: CallTool;
  /** Asks the host to save a file; without it, scores cannot be downloaded. */
  downloadFile?: DownloadFile | undefined;
  onBack?: () => void;
}) {
  const { t } = useTranslation();
  const [scores, setScores] = useState(data.scores);
  const [removed, setRemoved] = useState(false);
  const [deletion, setDeletion] = useState<Deletion | null>(null);
  const [outcome, setOutcome] = useState<Outcome>();
  const [transcription, setTranscription] = useState<TranscriptionOutcome>();
  const fileInput = useRef<HTMLInputElement>(null);
  const busy = outcome?.state === "waiting" || transcription?.state === "pending";

  async function perform(
    action: Action,
    task: () => Promise<undefined | "done" | "cancelled">,
  ): Promise<void> {
    setTranscription(undefined);
    setOutcome({ action, state: "waiting" });
    try {
      const state = await task();
      setOutcome({ action, state: state ?? "done" });
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

  const downloadScore =
    downloadFile &&
    ((score: ScoreInfo) => {
      void perform("download", async () => {
        const file = scoreFile(await callTool("download_score", { score_id: score.id }));
        if (file === undefined) throw new Error("The score file was not returned.");
        return downloadFile(file);
      });
    });

  async function transcribe(score: ScoreInfo) {
    setOutcome(undefined);
    setTranscription({ state: "pending" });
    try {
      const result = await requestTranscription(callTool, score.id);
      if (result.state === "done") {
        const recognized = result.score;
        setScores((previous) =>
          previous.some((entry) => entry.id === recognized.id)
            ? previous
            : [...previous, recognized],
        );
      }
      setTranscription(result);
    } catch {
      setTranscription({ state: "failed" });
    }
  }

  async function prepareDeletion(target: "work" | "score", id: string) {
    setTranscription(undefined);
    setOutcome({ action: "prepare-delete", state: "waiting" });
    try {
      const reply = await callTool(`preview_${target}_deletion`, { target_id: id });
      const preview = parseDeletionInfo(reply);
      if (preview?.status !== "pending") throw new Error("The deletion preview is unavailable.");
      setDeletion({ id, preview, refreshed: false });
      setOutcome(undefined);
    } catch {
      setOutcome({ action: "prepare-delete", state: "failed" });
    }
  }

  async function confirmDeletion() {
    if (deletion === null) return;
    setDeletion(null);
    setOutcome({ action: "delete", state: "waiting" });
    try {
      const reply = await callTool(CONFIRM_TOOL, { token: deletion.preview.token });
      const result = parseDeletionInfo(reply);
      if (result?.status === "pending") {
        setDeletion({ ...deletion, preview: result, refreshed: true });
        setOutcome(undefined);
        return;
      }
      if (result?.status !== "deleted") throw new Error("The deletion failed.");
      if (result.deletion.target === "work") setRemoved(true);
      else setScores((previous) => previous.filter((score) => score.id !== deletion.id));
      setOutcome({ action: "delete", state: "done" });
    } catch {
      setOutcome({ action: "delete", state: "failed" });
    }
  }

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
      {transcription?.state === "pending" && (
        <p role="status" aria-label={t("glossary.transcription")}>
          {t("view.loading")}
        </p>
      )}
      {transcription?.state === "done" && (
        <Alert variant="success">{t("work.transcriptionDone")}</Alert>
      )}
      {transcription?.state === "failed" && (
        <Alert variant="danger">
          {transcription.errorKey === "work.transcriptionInstall"
            ? t("work.transcriptionInstall")
            : transcription.errorKey === "work.transcriptionUnavailable"
              ? t("work.transcriptionUnavailable")
              : t("work.transcriptionFailed")}
          {transcription.installUrl && (
            <>
              {" "}
              <Alert.Link href={transcription.installUrl} target="_blank" rel="noopener noreferrer">
                Audiveris
              </Alert.Link>
            </>
          )}
        </Alert>
      )}
      {!removed && (
        <>
          <WorkDetails data={data} />
          <h2 className="h5">{t("deletion.scores")}</h2>
          <ScoreTable
            scores={scores}
            busy={busy}
            onOpen={openScore}
            onDownload={downloadScore}
            onTranscribe={
              data.supportsTranscription ? (score) => void transcribe(score) : undefined
            }
            onDelete={(score) => {
              void prepareDeletion("score", score.id);
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
                void prepareDeletion("work", data.work.id);
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
          {deletion?.refreshed && <Alert variant="info">{t("deletion.nothingDeleted")}</Alert>}
          {deletion && <DeletionSummaryView deletion={deletion.preview.deletion} />}
          {deletion?.preview.deletion.target === "work" && <p>{t("work.deleteWithScores")}</p>}
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
          <Button variant="danger" onClick={() => void confirmDeletion()}>
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
  if (outcome.state === "cancelled") {
    return <Alert variant="info">{t("work.downloadCancelled")}</Alert>;
  }
  if (outcome.state === "failed") {
    const message =
      outcome.action === "upload"
        ? t("work.uploadError")
        : outcome.action === "open"
          ? t("work.openError")
          : outcome.action === "download"
            ? t("work.downloadError")
            : t("deletion.failed");
    return <Alert variant="danger">{message}</Alert>;
  }
  const message =
    outcome.action === "upload"
      ? t("work.uploaded")
      : outcome.action === "open"
        ? t("work.opened")
        : outcome.action === "download"
          ? t("work.downloaded")
          : t("deletion.done");
  return <Alert variant="success">{message}</Alert>;
}
