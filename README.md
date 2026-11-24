# CI strategy demonstration with Azure DevOps

This project uses a deliberately small Python calculator to demonstrate **continuous integration (CI)** with Azure Pipelines. The application is not the focus: the aim is to show how automated checks and pull request (PR) reviews help a team integrate changes safely.

The same approach applies to data science and machine learning projects, where application code, tests, dependencies, containers and infrastructure all contribute to the quality of a solution.

## Why CI matters

CI checks changes early and consistently, rather than relying on someone remembering to run every check before a merge. A useful CI pipeline:

- **Catches defects early:** unit tests and linting give fast feedback while a change is still easy to fix.
- **Makes quality visible:** coverage and security checks highlight gaps and risks for the whole team.
- **Checks operational readiness:** container and deployment configuration checks catch problems beyond the application code.
- **Supports safer collaboration:** a required build and review provide a common, repeatable gate before changes reach `main`.

A passing pipeline is not proof that software is defect-free or secure. It is a baseline that should be complemented by meaningful reviews, suitable tests and monitoring.

## Shared responsibility

CI works best when the people writing code and the people operating the platform agree on the checks and help resolve failures.

| Responsibility | Typical owner | Purpose | Status in this demo |
| --- | --- | --- | --- |
| Unit tests | Developer / data scientist | Check that application behavior is correct. | `pytest` tests addition and subtraction, including negative numbers and zero. |
| Linting | Developer / data scientist | Identify code-quality issues. | `ruff check .` reports issues without changing files. |
| Formatting | Developer / data scientist | Keep code consistent and easier to review. | `black --check app tests` checks formatting without changing files. |
| Docker build | Platform / DevOps / MLOps engineer | Check that a container image can be built. | CI builds `calculator-app`; it does not push or run the image. |
| Helm validation | Platform / DevOps / MLOps engineer | Check a chart for common issues before deployment. | CI installs Helm and runs `helm lint`. |
| Terraform validation | Platform / DevOps / MLOps engineer | Check infrastructure configuration before applying it. | CI checks formatting, initializes without a backend, and validates a provider-free example. |
| Security scanning | Shared | Find known risks in dependencies and other components. | `pip-audit` checks the requirements and their resolved dependencies for known vulnerabilities. |
| Coverage checks | Shared | Highlight application code that tests do not exercise. | CI requires at least **70%** coverage of `app`. Coverage measures execution, not test quality. |

These are suggested primary responsibilities, not silos. Developers and data scientists own the behavior of their changes; platform and MLOps engineers help make checks reliable and deployable; everyone shares responsibility for security, coverage and fixing a failing PR.

## How the current pipeline works

The pipeline is defined in [`azure-pipelines.yaml`](azure-pipelines.yaml) and uses an Azure-hosted Ubuntu agent:

1. Select Python 3.11 and install the Python dependencies.
2. Check linting and formatting without modifying the checkout.
3. Run the unit tests and fail if coverage of `app` is below 70%.
4. Audit Python dependencies for known vulnerabilities.
5. Build the Docker image.
6. Install Helm and lint the chart.
7. Install Terraform, check formatting, initialize and validate the example configuration.

The YAML has `trigger: none` and a PR trigger targeting `main`: it is intended for PR validation rather than a continuous build on every push to `main`. With **GitHub** as the source repository, the YAML PR trigger can run for PRs targeting `main`. With **Azure Repos Git**, YAML PR triggers are not supported; configure a build-validation branch policy instead. In either case, configure the repository's merge policy separately: a trigger alone does not prevent an incomplete or failing PR from being merged.

The Terraform example uses the built-in `terraform_data` resource, so validation needs neither a cloud account nor credentials. It does not create real infrastructure, and the pipeline does not run `terraform apply`. Likewise, dependency scanning checks known Python package vulnerabilities; it is not a container, source-code or infrastructure security scan.

### Project layout

```text
app/                    Calculator functions
tests/                  Calculator unit tests
azure-pipelines.yaml    Azure Pipelines CI definition
Dockerfile              Container image definition
calculator-chart/       Example Helm chart
terraform/              Provider-free Terraform example
requirements.txt        Python dependencies and CI tools
```

The chart currently defaults to an `nginx` image, not the image built by CI. The calculator script prints messages and exits; it is not a web server. The Docker and Helm steps therefore demonstrate build and chart validation independently, not a working deployed calculator service.

## Run the checks locally

Run these commands from the project root. You need Python and pip; Docker, Helm and Terraform 1.4 or newer are needed for their respective checks. CI and the Dockerfile use Python 3.11.

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS or Linux, activate it with `source .venv/bin/activate` instead.

```bash
# Developer / data scientist checks
ruff check .
black --check app tests

# Shared checks
pytest --cov=app --cov-fail-under=70
pip-audit -r requirements.txt

# Platform / DevOps / MLOps checks
docker build -t calculator-app .
helm lint calculator-chart/
terraform -chdir=terraform fmt -check -recursive
terraform -chdir=terraform init -backend=false -input=false
terraform -chdir=terraform validate
```

To see the application output, run `python app/calculator.py`. To fix formatting locally, run `black app tests` and commit the resulting changes. The requirements are not pinned, so a dependency audit can change as new versions or vulnerabilities are published.

## Protecting `main` and validating pull requests

A typical workflow is:

```text
feature branch -> open PR to main -> CI checks + peer review -> merge after approval and passing checks
```

1. Create a short-lived feature branch and make a focused change.
2. Run the relevant checks locally and open a PR targeting `main`.
3. Let Azure Pipelines run the PR checks. Review the change and address feedback or failures; pushing fixes should trigger another validation.
4. Merge only when the required review and latest required checks pass.

The policy belongs to the repository hosting the code, while the pipeline runs in Azure DevOps. Choose the instructions for your repository host:

### GitHub repository with Azure Pipelines

1. In Azure DevOps, create a pipeline connected to the GitHub repository and select the existing `azure-pipelines.yaml`. Authorize the connection and ensure Azure Pipelines can report checks to GitHub.
2. Open a test PR targeting `main` and confirm that the Azure Pipelines check starts and reports its result to GitHub. The YAML PR trigger is configured for this case.
3. In the GitHub repository's **Settings > Rules > Rulesets**, create a branch ruleset targeting `main` (or use a branch protection rule).
4. Require a PR before merging, set the required number of approvals, and consider dismissing stale approvals when new commits are pushed.
5. Require status checks to pass and select the actual Azure Pipelines check reported by the test PR. Require the branch to be up to date if appropriate for the team. Restrict direct pushes and limit bypass permissions so the policy cannot be routinely bypassed.
6. Verify with a PR: a failing or pending required check, or a missing required approval, should block the merge. Fix the issue and confirm the merge becomes available after the required checks and review pass.

### Azure Repos Git alternative

1. Create an Azure pipeline using the existing YAML.
2. In **Repos > Branches**, open the `main` branch's **Branch policies**.
3. Configure the minimum number of reviewers and add the pipeline under **Build validation** as a required, automatically triggered policy. Configure build expiration so validation reflects changes to the target branch.
4. Limit permissions that allow direct pushes or bypassing policies, then verify the policy using a test PR.

The exact UI and available permissions can vary by organization and repository settings. In both hosts, make sure the required check is the intended pipeline and that the policy applies to `main`.

## References

- [Azure Pipelines: GitHub repositories and PR triggers](https://learn.microsoft.com/azure/devops/pipelines/repos/github)
- [Azure Repos branch policies](https://learn.microsoft.com/azure/devops/repos/git/branch-policies)
- [GitHub: managing rulesets](https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets)
