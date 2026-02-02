---
name: github-issues-generator
description: This skill ties in to the github-board-manager skill in this repository. Where this skill handles the generation of the content if the different types of issues, the github-board-manager is responsible for executing GitHub project board tasks. But, both work in harmony, tying in into each others workflows.

This skill generates GitHub issues and provides project board integration, in combination with the seperate skill "github-board-manager". It contains 4 workflows to generate 4 different types of GitHub issues. Epics, sub-epics, features, and tasks. For epics and sub-epics it is possible, but not necessary, to contain multiple user sories for different roles. Tasks are the smallest units of work. Epics can be a parent of sub-epics and features. Sub-epics are a child of an epic and have features as children. Features have an epic or sub-epic as a child and has tasks as children. Tasks have features as a parent.

Use when user wants to (1) create epics, sub-epics, features, or tasks. (2) Get context for the creation of new issues based on existing issues on the Github project board using the "github-board-manager" skill. (3) Create a new issue with sub-issues. (4) Add newly created issues to the Github project board using the "github-board-manager" skill. (5) Update existing Github issues using the "github-board-manager" skill. (6) Link issues to other issues as sub-issues using the "github-board-manager" skill. (7) Suggest missing features based on existing issues on the Github project board and trhe codebase in the repositories of the project. Triggers on phrases like "create an epic", "create a sub-epic", "create a new feature", "create new task".
---


# Workflows

## Workflow 1: Create new Epic
This workflow is for the generation of epic issues and post them on the GitHub project board using the "github-board-manager" skill workflow "Create epic". Epics connot have parents and are broken down into sub-epics and/or features. It features an elaborate template, trying to describe the problem context and solution space. THe workflow is as follows:

1. Ask the user for a title and a description to use for the new epic. Then check if the projectboard contains existing epic, features or user stories that relate or overlap with the intent of the new epic using the "github-board-manager" skill. If so, show the user a list of matching issues. Also, ask the user if they want to provide reference to issues that should relate to the new epic.

2. Then, improve the given description, based on the provided context, and make it more detailed and systematic. Write the new description into a markdown file in a top-level folder called "issue-drafts". Present the improved description to the user and give them the following options:

* Accept new description and create a full epic based on the format below.
* The user gets to provide instructions and corrections. Use this input to further improve the new description, and repeat asking the user for next steps.

3. After the epic has been approved, generate a list of candidate user stories. Only the user feature sentence/title. Present the user with the options, so the user can select one or more user stories for the epic. After this selection, generate and present the user with the full epic, according to the following template:

"
## Title

## Description

<!--Provide an elaborate description of the context of the epic. Describe the problem space and the solution space. Add relevant literature herre. -->

## So that …

<!--Give a title in User Story format.

Use a Subject Verb Object (SVO) word order (‘Students (S) read (V) books (O)’).
_S_ are the Stakeholder(s), and do not repeat these in this Description but exclusively list them as Stake Labels.
Fill in the … in ‘As (S), I want to …’, and keep your Description minimal (e.g., don’t repeat parts that aren't ‘…’).
For example, ‘As Student (S) I want to read (V) books (O)’.-->

## Attacker Story

<!--As a(n) [attacker type]…, I want to …, so that …

See https://owaspsamm.org/model/verification/requirements-driven-testing/stream-b/.-->

## Acceptance criteria

<!--Choose acceptance criteria from the acceptance criteria library.-->

<!--Add specific acceptance criteria where needed.-->

## Stakeholders and Users

<!--Label as appropriate.-->

This Child Epic was initially reported by …, and … The Stakeholders assigned in the Labels, have the following interests … Decision-makers or buyers are \\\[not\\\] involved, since …

<!--Use official names of Stakeholders as documented in e.g., the domain model.-->

## The User’s problem

To analyze and summarize the problem:

<!--Don’t simply quote the user.-->

## The impact of this problem on the User

<!--Relate the impact at minimum to the _Quality ✅_ Labels.-->

## The reach of this problem

<!--Requester will describe how many users will be positively impacted or leverage this feature.-->

## Business case

If this need is not addressed, this incurs the following **costs** on …:

- …
- …

If it is addressed, that will provide **value** in the following way:

- …

<!--To ensure consistency, only refer to commonly agreed business goals and risks such as 'increased support costs' or 'risk of losing partners'.-->

## User studies and supporting materials

<!--Validate the problem and desired outcome.-->

<!--User studies reports, metrics, illustrations, et cetera.-->
"

4. Now the present the user with the full epic and offer the following choices:

* Create the epic using the github-board-manager skill workflow "Create Epic".
* The user gets to provide instructions and corrections. Use this input to further improve the new description, and repeat asking the user for next steps.
* Add sub-epic(s) as an sub issue according to the workflow described below in the in the create sub-epic workflow.
* Add feature(s) as a sub-issues to the epic according to the workflow descibed below in the "Create feature" workflow.

## Workflow 2: Create new sub-epic

1. Ask the user for the title of the parent epic.
2. Retrieve the parent epic using the github-board-manager skill workflow "Retrieve issues". 
3. Confirm with the user if this is the right epic by showing the title, description and user sotry. If not approved retry. 
4. When approved, link the epic as a parent to the newly generated sub-epic.
5. Ask the user for a title and a description to use for the new sub-epic. 
6. Then check if the projectboard contains existing epics, sub-epics, features or tasks that relate or overlap with the intent of the new sub-epic using the "github-board-manager" skill workflow "Retreive issues". 
7. If so, show the user a list of matching issues. Also, ask the user if they want to provide reference to issues that should relate to the new sub-epic.
8. Improve the given description, based on the provided context, and make it more detailed and systematic. Write the new description into a markdown file in a top-level folder called "issue-drafts". Present the improved description to the user and give them the following options:

* Accept new description and create a full epic based on the format below.
* The user gets to provide instructions and corrections. Use this input to further improve the new description, and repeat asking the user for next steps.

9. After this selection, generate and present the user with the full epic, according to the following template:

"
## Title

## Description

<!--Provide an elaborate description of the context of the epic. Describe the problem space and the solution space. Add relevant literature herre. -->

## So that …

<!--Give a title in User Story format.

Use a Subject Verb Object (SVO) word order (‘Students (S) read (V) books (O)’).
_S_ are the Stakeholder(s), and do not repeat these in this Description but exclusively list them as Stake Labels.
Fill in the … in ‘As (S), I want to …’, and keep your Description minimal (e.g., don’t repeat parts that aren't ‘…’).
For example, ‘As Student (S) I want to read (V) books (O)’.-->

## Attacker Story

<!--As a(n) [attacker type]…, I want to …, so that …

See https://owaspsamm.org/model/verification/requirements-driven-testing/stream-b/.-->

## Acceptance criteria

<!--Choose acceptance criteria from the acceptance criteria library.-->

<!--Add specific acceptance criteria where needed.-->

## Stakeholders and Users

<!--Label as appropriate.-->

This Child Epic was initially reported by …, and … The Stakeholders assigned in the Labels, have the following interests … Decision-makers or buyers are \\\[not\\\] involved, since …

<!--Use official names of Stakeholders as documented in e.g., the domain model.-->

## The User’s problem

To analyze and summarize the problem:

<!--Don’t simply quote the user.-->

## The impact of this problem on the User

<!--Relate the impact at minimum to the _Quality ✅_ Labels.-->

## The reach of this problem

<!--Requester will describe how many users will be positively impacted or leverage this feature.-->

## Business case

If this need is not addressed, this incurs the following **costs** on …:

- …
- …

If it is addressed, that will provide **value** in the following way:

- …

<!--To ensure consistency, only refer to commonly agreed business goals and risks such as 'increased support costs' or 'risk of losing partners'.-->

## User studies and supporting materials

<!--Validate the problem and desired outcome.-->

<!--User studies reports, metrics, illustrations, et cetera.-->
"

10. Ask for confirmation to do the following:

* Post the new sub-epic and link it to the porposed parent epic as a the parent to this newly created sub-epic on the github project board using the github-board-manager skill workflow create sub-epic.

11. Use the github-board-manager skill workflow "create sub-epic" to create the new sub-epic and link it to the chosen epic.

## Workflow 3: Create new Feature
This workflow is for the generation of feature issues and post them on the GitHub project board using the "github-board-manager" skill. Features need to have an epic or sub-epic as a parent and is broken down into tasks. It features a different, more simple, template then the template of epics and sub-epics. It should describe a concrete user value, adding to the more general value described in its parent epic or sub-epic. The workflow is as follows:

1. Ask the title of the parent (sub-)epic of which it the newly created feature needs to be a sub-issue.
2. Retrieve the parent epic using the github-board-manager skill workflow "Retrieve issues".
3. Confirm with the user if this is the right (sub-)epic by showing the title, description and user sotry. If not approved retry. 
4. When approved, link the epic or sub-epic as a parent to the new feature.
5. Ask the user for a title and a description to use for the new feature. 
6. Use the "github-board-manager" skill workflow "Retreive issues" to check if the projectboard contains existing epics, sub-epic, features or tasks that relate or overlap with the intent of the feature, . 
7. If so, show the user a list of matching issues. Also, ask the user if they want to provide reference to issues that should relate to the feature.
8. Improve the given description, based on the provided context, and make it more detailed and systematic. Write the new description into a markdown file in a top-level folder called "issue-drafts". Present the improved description to the user and give them the following options:

* Accept new description and generate full feature based on the format below.
* The user gets to provide instructions and corrections. Use this input to further improve the new description, and repeat asking the user for next steps.

9. 10. After this selection, generate and present the user with the full feature, according to the following template:

"
## Description

<!--Give a short description of the feature and some context on how it came about-->

## ..., so that...

<!--Give a title in User Story format.

Use a Subject Verb Object (SVO) word order (‘Students (S) read (V) books (O)’).
_S_ are the Stakeholder(s), and do not repeat these in this Description but exclusively list them as Stake Labels.
Fill in the … in ‘As (S), I want to …’, and keep your Description minimal (e.g., don’t repeat parts that aren't ‘…’).
For example, ‘As Student (S) I want to read (V) books (O)’.-->

## Acceptance criteria

<!--Specify the acceptance criteria for the feature. Try to make them as concrete as possible.-->

<!--[optional] If it can be directly translated into a task, this is to be preferred-->

[ ] ...
"

9. After the feasture has been generated, show it to the user and present the user with the following options:

* Accept the feature and the linked parent epic and create it on the Github project board using the github-board-manager skill workflow "Create feature".
* Select a different epic as a parent by the title on the Github project board and link it to the newly generated feature.

10. Use the github-board-manager skill workflow "create feature" to create the new feature and link it to the chosen epic or sub-epic.

### Create new Task
This workflow is for generating tasks, the smallest unit of work. Tasks describe concrete functionalities that need to be implemented for the value described in the feature to be realized. Tasks need to have a feature as a parent. The template is very simple and mainly consists of requirements. The workflow is as follows.

1. Ask the title of the parent feature of which it the newly created task needs to be a sub-issue.
2. Retrieve the parent feature using the github-board-manager skill workflow "Retrieve issues".
3. Confirm with the user if this is the right feature by showing the title, description and user story. If not approved retry. 
5. When approved. linkt the feature as a parent for the newly created task.
4. Based on the provided context, improve the given description and provide the needed requirements for the described functionality. Write the new description and requirements into a markdown file in a top-level folder called "issue-drafts". Present the improved description to the user and give them the following options:

* Accept new description and generate full feature based on the format below.
* The user gets to provide instructions and corrections. Use this input to further improve the new description, and repeat asking the user for next steps.

5. When approved, use the geithub-board-manager to post the task as an sub-issue of the chosen feature parent to the new feature.



## Advanced Reference

For complete documentation including migration workflows, bulk operations, and troubleshooting, see: [references/github-issue-manager-reference.md](references/github-issue-manager-reference.md)
