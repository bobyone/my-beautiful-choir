// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

import { useState } from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";
import Pagination from "react-bootstrap/Pagination";
import Table from "react-bootstrap/Table";
import { useTranslation } from "react-i18next";

import type { CallTool } from "../viewData";
import { parseWorkResult, type WorkResult } from "../work/workInfo";
import { WorkPanel } from "../work/WorkPanel";
import { parseRepertoire, type RepertoireInfo } from "./repertoireInfo";

export function RepertoirePanel({ data, callTool }: { data: RepertoireInfo; callTool: CallTool }) {
  const { t, i18n } = useTranslation();
  const [repertoire, setRepertoire] = useState(data);
  const [search, setSearch] = useState(data.search);
  const [selectedWork, setSelectedWork] = useState<WorkResult>();
  const [state, setState] = useState<"idle" | "loading" | "error">("idle");
  const busy = state === "loading";
  const collator = new Intl.Collator(i18n.language);
  const totals = new Intl.NumberFormat(i18n.language);

  async function searchRepertoire(choir: string, text: string, page?: number): Promise<void> {
    setState("loading");
    try {
      const reply = await callTool(
        "show_repertoire",
        page === undefined
          ? { choir, search: text, page_size: repertoire.pageSize }
          : { choir, search: text, page, page_size: repertoire.pageSize },
      );
      const updated = parseRepertoire(reply);
      if (!updated) throw new Error("The repertoire reply was invalid.");
      setRepertoire(updated);
      setState("idle");
    } catch {
      setState("error");
    }
  }

  async function showWork(id: string): Promise<void> {
    setState("loading");
    try {
      const reply = await callTool("show_work", { work_id: id });
      const work = parseWorkResult(reply);
      if (!work) throw new Error("The work reply was invalid.");
      setSelectedWork(work);
      setState("idle");
    } catch {
      setState("error");
    }
  }

  const choir = repertoire.choir;
  if (selectedWork !== undefined) {
    return (
      <WorkPanel
        key={selectedWork.work.id}
        data={selectedWork}
        callTool={callTool}
        onBack={() => {
          setSelectedWork(undefined);
          if (choir !== null) void searchRepertoire(choir, repertoire.search, repertoire.page);
        }}
      />
    );
  }

  return (
    <section className="p-3" aria-labelledby="repertoire-heading">
      <h1 id="repertoire-heading" className="h4">
        {t("glossary.repertoire")}
      </h1>
      {choir === null ? (
        <p>{t("repertoire.noChoirs")}</p>
      ) : (
        <>
          <h2 className="h5">{choir}</h2>
          <Form
            className="row g-2 mb-3"
            onSubmit={(event) => {
              event.preventDefault();
              if (!busy) void searchRepertoire(choir, search);
            }}
          >
            <Form.Group className="col-sm" controlId="repertoire-choir">
              <Form.Label>{t("glossary.choir")}</Form.Label>
              <Form.Select
                value={choir}
                disabled={busy}
                onChange={(event) => {
                  void searchRepertoire(event.currentTarget.value, search);
                }}
              >
                {repertoire.choirs.toSorted(collator.compare).map((name) => (
                  <option key={name}>{name}</option>
                ))}
              </Form.Select>
            </Form.Group>
            <Form.Group className="col-sm" controlId="repertoire-search">
              <Form.Label>{t("repertoire.search")}</Form.Label>
              <div className="d-flex gap-2">
                <Form.Control
                  type="search"
                  value={search}
                  disabled={busy}
                  maxLength={200}
                  onChange={(event) => {
                    setSearch(event.currentTarget.value);
                  }}
                />
                <Button type="submit" disabled={busy}>
                  {t("repertoire.search")}
                </Button>
              </div>
            </Form.Group>
          </Form>
          {busy && <p role="status">{t("view.loading")}</p>}
          {state === "error" && <Alert variant="danger">{t("view.error")}</Alert>}
          {repertoire.works.length === 0 ? (
            <p>{t("repertoire.noWorks")}</p>
          ) : (
            <>
              <p>{t("repertoire.workCount", { workCount: repertoire.workCount })}</p>
              <Table responsive striped>
                <caption className="visually-hidden">{t("deletion.works")}</caption>
                <thead>
                  <tr>
                    <th scope="col">{t("glossary.title")}</th>
                    <th scope="col">{t("glossary.composer")}</th>
                    <th scope="col">{t("glossary.voicing")}</th>
                    <th scope="col">{t("deletion.scores")}</th>
                  </tr>
                </thead>
                <tbody>
                  {repertoire.works.map((work) => (
                    <tr key={work.id}>
                      <th scope="row">
                        <Button
                          variant="link"
                          className="p-0 text-start"
                          disabled={busy}
                          onClick={() => {
                            void showWork(work.id);
                          }}
                        >
                          {work.title}
                        </Button>
                      </th>
                      <td>{work.composer}</td>
                      <td>{work.voicing}</td>
                      <td>{totals.format(work.scoreCount)}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
              {repertoire.pageCount > 1 && (
                <nav aria-label={t("repertoire.pages")}>
                  <Pagination className="flex-wrap">
                    <Pagination.Item
                      disabled={busy || repertoire.page === 1}
                      onClick={() => {
                        void searchRepertoire(choir, repertoire.search, repertoire.page - 1);
                      }}
                    >
                      {t("repertoire.previousPage")}
                    </Pagination.Item>
                    <Pagination.Item active activeLabel="" aria-current="page">
                      {t("repertoire.pageOf", {
                        page: repertoire.page,
                        pageCount: repertoire.pageCount,
                      })}
                    </Pagination.Item>
                    <Pagination.Item
                      disabled={busy || repertoire.page === repertoire.pageCount}
                      onClick={() => {
                        void searchRepertoire(choir, repertoire.search, repertoire.page + 1);
                      }}
                    >
                      {t("repertoire.nextPage")}
                    </Pagination.Item>
                  </Pagination>
                </nav>
              )}
            </>
          )}
        </>
      )}
    </section>
  );
}
