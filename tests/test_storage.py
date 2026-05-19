from paperforge.storage import research_job_from_dict


def test_research_job_from_dict_supports_legacy_camel_case_jobs():
    job = research_job_from_dict(
        {
            "id": "job-1",
            "input": "https://arxiv.org/abs/1706.03762",
            "status": "completed",
            "paperSlug": "attention-is-all-you-need",
            "createdAt": "2026-05-16T13:28:35.052Z",
            "updatedAt": "2026-05-16T13:28:35.052Z",
            "metadata": {
                "slug": "attention-is-all-you-need",
                "title": "Attention Is All You Need",
                "authors": ["Ashish Vaswani"],
                "canonicalUrl": "http://arxiv.org/abs/1706.03762v7",
                "pdfUrl": "https://arxiv.org/pdf/1706.03762v7",
                "sourceUrl": "https://arxiv.org/e-print/1706.03762v7",
                "githubCandidates": [],
                "createdAt": "2026-05-16T13:28:35.048Z",
                "status": "intake_completed",
            },
            "steps": [
                {
                    "id": "intake.resolve_identity",
                    "name": "Resolve paper identity",
                    "state": "completed",
                    "startedAt": "2026-05-16T13:28:34.644Z",
                    "endedAt": "2026-05-16T13:28:35.048Z",
                }
            ],
            "artifacts": [],
        }
    )

    assert job.input_text == "https://arxiv.org/abs/1706.03762"
    assert job.paper_slug == "attention-is-all-you-need"
    assert job.metadata is not None
    assert job.metadata.pdf_url == "https://arxiv.org/pdf/1706.03762v7"
    assert job.steps[0].started_at == "2026-05-16T13:28:34.644Z"

