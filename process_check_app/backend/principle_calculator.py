from collections import defaultdict

# Global variables for all_yes_desc and not_all_yes_desc
ALL_YES_DESC = """
Company indicated that it was able to produce
documentary evidence for all the items required under
this principle.
"""

NOT_ALL_YES_DESC = """
Company indicated that it did not implement all the
processes under this principle, or the processes were not
applicable to the AI system tested:
"""


# Define the transparency_principle function
def transparency_principle(data):
    transparency_all_yes_wim = [
        """
    Company has put in place communication mechanisms in
    a manner appropriate to the use case at hand and
    accessible to the audience, to enable those using and/or
    affected by the AI system to understand how their data is
    collected and used, and the intended use and limitations
    of the AI system.
    """
    ]

    transparency_not_all_yes_wim = [
        """
    Without implementing all the measures and practices
    specified under this principle, there may be a risk that the
    desired outcomes of this principle would not be fully
    achieved.
    """
    ]

    transparency_recommendation = """
    Company should periodically review the justifications for
    not implementing certain measures and practices
    specified under this principle to ensure that they are still
    valid and applicable given the current circumstances.
    <br/><br/>Company can also consider consulting the users
    interacting with or individuals affected by the AI system
    to find out if the current level of information provided to
    them is adequate, and if not, can consider implementing
    the processes in the testing framework
    """

    process_to_achieve_outcomes = []

    summary_justification = []

    # Check the implementation status for the transparency principle
    all_yes = True
    for principle_id, processes in data["process_checks"].items():
        for process_id, details in processes.items():
            if details["principle_key"].strip() == "1. Transparency":
                if details["implementation"] != "Yes":
                    all_yes = False
                    process_to_achieve_outcomes.append(
                        details["process_to_achieve_outcomes"].replace("\n", "<br/>")
                    )
                    # Append justification from elaboration if "No" or "N/A" and elaboration is not empty
                    elaboration = details.get("elaboration", "").strip()
                    if elaboration:
                        summary_justification.append(elaboration)

    # Update the JSON with the appropriate description or WIM
    if all_yes:
        data["transparency_description"] = ALL_YES_DESC
        data["transparency_wim"] = transparency_all_yes_wim
        data["transparency_recommendation"] = ""
    else:
        data["transparency_description"] = NOT_ALL_YES_DESC
        data["transparency_wim"] = transparency_not_all_yes_wim
        data["transparency_recommendation"] = transparency_recommendation

    # Append the outcome descriptions for "No" or "N/A"
    data["process_to_achieve_outcomes"] = process_to_achieve_outcomes
    # Add the justifications, set to None if empty
    data["justifications"] = summary_justification if summary_justification else None

    return data


# Define the explainability_principle function
def explainability_principle(data):
    explainability_all_yes_wim = [
        """
    Company has demonstrated a preference for developing AI
    systems that can better explain their output (e.g., using
    foundation models with open weights) or that are
    interpretable by default (e.g., modelling with decision
    trees).
    """
    ]

    explainability_not_all_yes_wim = [
        """
    When it can be established that the performance of
    different models under consideration are similar, by not
    choosing the more explainable models for deployment,
    Company runs the risk of not being able to help its
    stakeholders understand how the AI system produces its
    output.
    <br/><br/>The ability to offer reasonable explanations for AI-
    generated output can improve stakeholder trust and
    acceptance.
    """
    ]

    explainability_recommendation = """
    Company should consider the prevailing regulatory
    requirements relevant to this principle, its own internal
    policies and the intended use of the AI model and
    determine if such risk is acceptable. When building or
    procuring AI systems, adopt a principle of “explainability
    by design” — default to interpretable models where
    performance trade-offs are acceptable.
    """

    process_to_achieve_outcomes = []

    summary_justification = []

    # Check the implementation status for the explainability principle
    all_yes = True
    for principle_id, processes in data["process_checks"].items():
        for process_id, details in processes.items():
            if details["principle_key"].strip() == "2. Explainability":
                if details["implementation"] != "Yes":
                    all_yes = False
                    process_to_achieve_outcomes.append(
                        details["process_to_achieve_outcomes"].replace("\n", "<br/>")
                    )
                    # Append justification from elaboration if "No" or "N/A" and elaboration is not empty
                    elaboration = details.get("elaboration", "").strip()
                    if elaboration:
                        summary_justification.append(elaboration)

    # Update the JSON with the appropriate description or WIM
    if all_yes:
        data["explainability_description"] = ALL_YES_DESC
        data["explainability_wim"] = explainability_all_yes_wim
        data["explainability_recommendation"] = ""
    else:
        data["explainability_description"] = NOT_ALL_YES_DESC
        data["explainability_wim"] = explainability_not_all_yes_wim
        data["explainability_recommendation"] = explainability_recommendation

    # Append the outcome descriptions for "No" or "N/A"
    data["process_to_achieve_outcomes"] = process_to_achieve_outcomes
    # Add the justifications, set to None if empty
    data["justifications"] = summary_justification if summary_justification else None

    return data


def reproducibility_principle(data):
    reproducibility_all_yes_wim = [
        """
    Company has put in place measures and processes to
    enable the AI system to consistently perform its required
    functions under stated conditions for a specific period of
    time, and is also able to trace back and identify errors
    from logging.
    """
    ]
    reproducibility_not_all_yes_wim = [
        """
    Company may not be able to demonstrate consistency of
    the AI system’s behavior under stated conditions, and/or
    identify issues and problems in order to address them.
    """
    ]

    traceability_no_wim = [
        """
    <br/>This may affect the company’s ability to respond to internal
    queries, audits, or customer complaints — especially in high-stakes or
    regulated domains. Having foundational traceability practices in place
    can help future-proof the organisation’s AI operations for certification,
    due diligence, or regulatory alignment.
    """
    ]
    traceability_questions = ["3.1.1", "3.2.1", "3.3.1", "3.4.1"]
    reproductibility_questions = [
        "3.5.1",
        "3.6.1",
        "3.7.1",
        "3.8.1",
        "3.9.1",
        "3.10.1",
        "3.11.1",
        "3.12.1",
    ]

    reproducibility_no_wim = [
        """
    <br/>Without reproducibility, it may be difficult to identify,
    debug issues, or transition AI systems across teams or
    environments.
    """
    ]

    reproducibility_recommendation = """
    Company should consider the prevailing regulatory
    requirements relevant to this principle, its own internal
    policies and the intended use of the AI system and determine
    if such risk is acceptable. Logging is a foundational practice
    that supports the development, maintenance, and
    improvement of both generative and traditional AI systems. It
    ensures these systems are reliable, secure, and continuously
    evolving to meet user needs.
    """

    process_to_achieve_outcomes = []
    summary_justification = []
    all_yes = True
    wim = reproducibility_not_all_yes_wim.copy()

    # Check the implementation status for the reproducibility principle
    for principle_id, processes in data["process_checks"].items():
        for process_id, details in processes.items():
            if details["principle_key"].strip() == "3. Reproducibility":
                if details["implementation"] != "Yes":
                    all_yes = False
                    process_to_achieve_outcomes.append(
                        details["process_to_achieve_outcomes"].replace("\n", "<br/>")
                    )
                    elaboration = details.get("elaboration", "").strip()
                    if elaboration:
                        summary_justification.append(elaboration)
                    if (
                        process_id in traceability_questions
                        and traceability_no_wim[0] not in wim
                    ):
                        wim.extend(traceability_no_wim)
                    elif (
                        process_id in reproductibility_questions
                        and reproducibility_no_wim[0] not in wim
                    ):
                        wim.extend(reproducibility_no_wim)

    # Update the JSON with the appropriate description or WIM
    if all_yes:
        data["reproducibility_description"] = ALL_YES_DESC
        data["reproducibility_wim"] = reproducibility_all_yes_wim
        data["reproducibility_recommendation"] = ""
    else:
        data["reproducibility_description"] = NOT_ALL_YES_DESC
        data["reproducibility_wim"] = wim
        data["reproducibility_recommendation"] = reproducibility_recommendation

    # Append the outcome descriptions for "No" or "N/A"
    data["process_to_achieve_outcomes"] = process_to_achieve_outcomes
    # Add the justifications, set to None if empty
    data["justifications"] = summary_justification if summary_justification else None

    return data


def safety_principle(data):
    safety_all_yes_wim = [
        """
    Company has conducted assessments on the materiality
    and risk of harm on its stakeholders, identified and
    mitigated known risks. Company has also assessed that
    the residual risks of AI system is acceptable.
    """
    ]
    safety_not_all_yes_wim = [
        """
    Without implementing all the processes, the AI system may carry risk of harm to end users
    or individuals, which could have been mitigated. This could reduce the overall trust in the AI system.
    <br/><br/>Without a structured approach to assessing and monitoring risk,
    Company may not be aware of potential system failure points,
    safety harm, or unacceptable performance deviations.
    """
    ]

    set_1_wim = [
        """
    In the absence of strong content safety and validation
    processes, there is a risk that the AI system may output
    misleading, harmful, or non-compliant content. This
    would be a cause for concern especially for public-facing
    applications.
    """
    ]
    set_2_wim = [
        """
    The lack of Test, Evaluation, Verification, and Validation
    (TEVV practices) can also weaken internal and external
    confidence in the system’s reliability.
    """
    ]

    safety_recommendation = """
    Company should periodically review the justifications for
    not implementing certain measures and practices
    specified under this principle to ensure that they are still
    valid and applicable given the current circumstances.
    """

    safety_question_1 = ["4.8.1", "4.9.1", "4.9.2"]
    safety_question_2 = ["4.10.1", "4.10.2"]

    process_to_achieve_outcomes = []
    summary_justification = []
    all_yes = True
    wim = safety_not_all_yes_wim.copy()

    # Check the implementation status for the safety principle
    for principle_id, processes in data["process_checks"].items():
        for process_id, details in processes.items():
            if details["principle_key"].strip() == "4. Safety":
                if details["implementation"] != "Yes":
                    all_yes = False
                    process_to_achieve_outcomes.append(
                        details["process_to_achieve_outcomes"].replace("\n", "<br/>")
                    )
                    elaboration = details.get("elaboration", "").strip()
                    if elaboration:
                        summary_justification.append(elaboration)
                    if process_id in safety_question_1 and set_1_wim[0] not in wim:
                        wim.extend(set_1_wim)
                    elif process_id in safety_question_2 and set_2_wim[0] not in wim:
                        wim.extend(set_2_wim)

    # Update the JSON with the appropriate description or WIM
    if all_yes:
        data["safety_description"] = ALL_YES_DESC
        data["safety_wim"] = safety_all_yes_wim
        data["safety_recommendation"] = ""
    else:
        data["safety_description"] = NOT_ALL_YES_DESC
        data["safety_wim"] = wim
        data["safety_recommendation"] = safety_recommendation

    # Append the outcome descriptions for "No" or "N/A"
    data["process_to_achieve_outcomes"] = process_to_achieve_outcomes
    # Add the justifications, set to None if empty
    data["justifications"] = summary_justification if summary_justification else None

    return data


def security_principle(data):
    security_all_yes_wim = [
        """
    Company is able to provide certain level of assurance that
    the security of AI system is maintained, i.e. the protection
    of AI systems, their data, and the associated infrastructure
    from unauthorised access, disclosure, modification,
    destruction, or disruption.
    """
    ]
    security_not_all_yes_wim = [
        """
    Without implementing all the processes, Company’s AI
    system may be vulnerable to exploitation by malicious
    actors, resulting in the compromise of its AI system’s
    confidentiality, integrity and availability. This, in turn,
    could cause damage and harm to both the end users and
    the owner of the AI system, including privacy violations,
    fraud, reputational damage, and potential regulatory
    challenges.
    """
    ]
    security_recommendation = """
    Security is essential in building stakeholder trust in the AI
    system. Company should periodically review the
    justifications for not implementing certain measures and
    processes under this principle to see if they are still valid.
    Security threats are fast evolving. It is further
    recommended that company should regularly assess
    security risks and take appropriate actions to continually
    stay up-to-date.
    """

    process_to_achieve_outcomes = []
    summary_justification = []
    all_yes = True
    wim = security_not_all_yes_wim.copy()

    # Check the implementation status for the security principle
    for principle_id, processes in data["process_checks"].items():
        for process_id, details in processes.items():
            if details["principle_key"].strip() == "5. Security":
                if details["implementation"] != "Yes":
                    all_yes = False
                    process_to_achieve_outcomes.append(
                        details["process_to_achieve_outcomes"].replace("\n", "<br/>")
                    )
                    elaboration = details.get("elaboration", "").strip()
                    if elaboration:
                        summary_justification.append(elaboration)

    # Update the JSON with the appropriate description or WIM
    if all_yes:
        data["security_description"] = ALL_YES_DESC
        data["security_wim"] = security_all_yes_wim
        data["security_recommendation"] = ""
    else:
        data["security_description"] = NOT_ALL_YES_DESC
        data["security_wim"] = wim
        data["security_recommendation"] = security_recommendation

    # Append the outcome descriptions for "No" or "N/A"
    data["process_to_achieve_outcomes"] = process_to_achieve_outcomes
    # Add the justifications, set to None if empty
    data["justifications"] = summary_justification if summary_justification else None

    return data


def robustness_principle(data):
    robustness_all_yes_wim = [
        """
    Company is able to demonstrate that the AI system under
    test is resilient against attacks and attempts at
    manipulation by third party malicious actors, and can still
    function without producing undesirable output despite
    unexpected input.
    """
    ]
    robustness_not_all_yes_wim = [
        """
    Without implementing all the processes, Company may
    not be able to identify factors that lead to AI system’s low
    level of accuracy, including detecting and mitigating
    adversarial attacks on the AI system. This may result in
    damaging consequences to Company’s stakeholders.
    <br/><br/>In the absence of ensuring robustness, systems may
    become vulnerable to silent failures or targeted
    manipulation. System may be degraded over time, which
    can accumulate into reliability or trust issues.
    """
    ]
    robustness_recommendation = """
    Robustness is essential for ensuring that both generative
    and traditional AI systems are reliable and capable of
    adapting to changing conditions and requirements. It
    plays a key role in building user trust, maintaining
    performance, and ensuring the ethical and safe operation
    of AI applications. Company should periodically review
    the justifications for not implementing certain measures
    and processes under this principle to see if they are still
    valid.
    """

    process_to_achieve_outcomes = []
    summary_justification = []
    all_yes = True
    wim = robustness_not_all_yes_wim.copy()

    # Check the implementation status for the robustness principle
    for principle_id, processes in data["process_checks"].items():
        for process_id, details in processes.items():
            if details["principle_key"].strip() == "6. Robustness":
                if details["implementation"] != "Yes":
                    all_yes = False
                    process_to_achieve_outcomes.append(
                        details["process_to_achieve_outcomes"].replace("\n", "<br/>")
                    )
                    elaboration = details.get("elaboration", "").strip()
                    if elaboration:
                        summary_justification.append(elaboration)

    # Update the JSON with the appropriate description or WIM
    if all_yes:
        data["robustness_description"] = ALL_YES_DESC
        data["robustness_wim"] = robustness_all_yes_wim
        data["robustness_recommendation"] = ""
    else:
        data["robustness_description"] = NOT_ALL_YES_DESC
        data["robustness_wim"] = wim
        data["robustness_recommendation"] = robustness_recommendation

    # Append the outcome descriptions for "No" or "N/A"
    data["process_to_achieve_outcomes"] = process_to_achieve_outcomes
    # Add the justifications, set to None if empty
    data["justifications"] = summary_justification if summary_justification else None

    return data


def fairness_principle(data):
    fairness_all_yes_wim = [
        """
    Company has put in place measures and processes to
    enable it to monitor, review and identify causes of model
    bias and address them accordingly.
    """
    ]
    fairness_not_all_yes_wim = [
        (
            "Without implementing all the processes, Company runs the risk of not "
            "being able to monitor and identify potential causes of bias and address "
            "them throughout the AI system’s lifecycle. <br/><br/>Without systematic fairness "
            "testing or representative data checks, the AI system may inadvertently "
            "underperform for certain user groups. This may result in discriminatory "
            "outcomes for individuals affected by the AI system. The absence of "
            "defined fairness criteria and sensitive features can make it difficult "
            "to align with emerging AI governance requirements (e.g., non-discrimination "
            "clauses, algorithmic accountability laws). This could also reduce overall "
            "trust in the system."
        )
    ]
    fairness_recommendation = """
    Fairness is essential for ensuring that both generative and
    traditional AI systems are ethical, trustworthy, and
    effective in serving diverse user groups. It plays a key role
    in mitigating bias, complying with regulations, and
    promoting positive social impact. Company should
    periodically review the justifications for not
    implementing certain measures and processes under this
    principle to see if they are still valid.
    """

    process_to_achieve_outcomes = []
    summary_justification = []
    all_yes = True

    # Check the implementation status for the fairness principle
    for principle_id, processes in data["process_checks"].items():
        for process_id, details in processes.items():
            if details["principle_key"].strip() == "7. Fairness":
                if details["implementation"] != "Yes":
                    all_yes = False
                    process_to_achieve_outcomes.append(
                        details["process_to_achieve_outcomes"].replace("\n", "<br/>")
                    )
                    elaboration = details.get("elaboration", "").strip()
                    if elaboration:
                        summary_justification.append(elaboration)

    # Update the JSON with the appropriate description or WIM
    if all_yes:
        data["fairness_description"] = ALL_YES_DESC
        data["fairness_wim"] = fairness_all_yes_wim
        data["fairness_recommendation"] = ""
    else:
        data["fairness_description"] = NOT_ALL_YES_DESC
        data["fairness_wim"] = fairness_not_all_yes_wim
        data["fairness_recommendation"] = fairness_recommendation

    # Append the outcome descriptions for "No" or "N/A"
    data["process_to_achieve_outcomes"] = process_to_achieve_outcomes
    # Add the justifications, set to None if empty
    data["justifications"] = summary_justification if summary_justification else None

    return data


def data_governance_principle(data):
    data_governance_all_yes_wim = [
        """
    Company has put in place measures and processes to
    govern the use of data in AI systems throughout the data
    lifecycle, including putting in place good governance
    practices for data quality, lineage, and to comply with
    relevant regulatory requirements or industry standards.
    """
    ]
    data_governance_not_all_yes_wim = [
        """
    Without implementing all the processes, Company runs
    the risk of potential data quality issues affecting accuracy
    of the AI system, bias issues relating to unintended
    discrimination, data security risks. Without clear lineage
    and sustained quality controls, it becomes harder to
    ensure that data used for AI remains appropriate,
    accurate, and compliant over time.
    <br/><br/>Gaps in oversight over third-party data usage may
    introduce avoidable risks, such as unauthorised use of
    proprietary data, or inconsistent application of internal
    data standards across teams and vendors.
    <br/>This may result in unauthorized access, use or disclosure
    and/or compliance issues with data protection regulations
    and laws.
    """
    ]
    data_governance_recommendation = """
    Company should review the reasons for not implementing
    certain processes and assess if these reasons are still valid.
    Company should review its data governance policy and
    explore putting in place relevant standards, guidelines
    and best practices.
    """

    process_to_achieve_outcomes = []
    summary_justification = []
    all_yes = True

    # Check the implementation status for the data governance principle
    for principle_id, processes in data["process_checks"].items():
        for process_id, details in processes.items():
            if details["principle_key"].strip() == "8. Data Governance":
                if details["implementation"] != "Yes":
                    all_yes = False
                    process_to_achieve_outcomes.append(
                        details["process_to_achieve_outcomes"].replace("\n", "<br/>")
                    )
                    elaboration = details.get("elaboration", "").strip()
                    if elaboration:
                        summary_justification.append(elaboration)

    # Update the JSON with the appropriate description or WIM
    if all_yes:
        data["data_governance_description"] = ALL_YES_DESC
        data["data_governance_wim"] = data_governance_all_yes_wim
        data["data_governance_recommendation"] = ""
    else:
        data["data_governance_description"] = NOT_ALL_YES_DESC
        data["data_governance_wim"] = data_governance_not_all_yes_wim
        data["data_governance_recommendation"] = data_governance_recommendation

    # Append the outcome descriptions for "No" or "N/A"
    data["process_to_achieve_outcomes"] = process_to_achieve_outcomes
    # Add the justifications, set to None if empty
    data["justifications"] = summary_justification if summary_justification else None

    return data


def accountability_principle(data):
    accountability_all_yes_wim = [
        """
    Company has put in place an organisational structure and
    internal governance mechanism to ensure clear roles and
    responsibilities for the use of AI. This allows the
    Company to quickly establish accountability when
    something goes wrong, identify the problem, and address
    it in a timely manner.
    """
    ]
    accountability_not_all_yes_wim = [
        """
    The current organisational structure and internal
    governance mechanism may not provide sufficient
    accountability and oversight of AI system.
    <br/><br/>Without clear internal roles, system inventories, and
    phase-out policies, there is a risk that AI systems continue
    to operate without active oversight — or that handoffs
    between teams and vendors create gaps in accountability.
    <br/><br/>A lack of auditability, especially for third-party or opaque
    systems, makes it difficult to investigate issues or
    demonstrate governance to stakeholders.
    <br/><br/>This may have negative impact on the identification and
    mitigation of risks associated with this AI system. This
    may also complicate remediation when issues arise.
    """
    ]
    accountability_recommendation = """
    Company should review the current organizational
    structure and internal governance mechanism to ensure
    clear accountability for those involved in Company’s AI
    development and deployment. It will be important for
    Company to clarify roles across the AI supply chain,
    ensuring all relevant parties are aware of their
    responsibilities.
    """

    process_to_achieve_outcomes = []
    summary_justification = []
    all_yes = True

    # Check the implementation status for the accountability principle
    for principle_id, processes in data["process_checks"].items():
        for process_id, details in processes.items():
            if details["principle_key"].strip() == "9. Accountability":
                if details["implementation"] != "Yes":
                    all_yes = False
                    process_to_achieve_outcomes.append(
                        details["process_to_achieve_outcomes"].replace("\n", "<br/>")
                    )
                    elaboration = details.get("elaboration", "").strip()
                    if elaboration:
                        summary_justification.append(elaboration)

    # Update the JSON with the appropriate description or WIM
    if all_yes:
        data["accountability_description"] = ALL_YES_DESC
        data["accountability_wim"] = accountability_all_yes_wim
        data["accountability_recommendation"] = ""
    else:
        data["accountability_description"] = NOT_ALL_YES_DESC
        data["accountability_wim"] = accountability_not_all_yes_wim
        data["accountability_recommendation"] = accountability_recommendation

    # Append the outcome descriptions for "No" or "N/A"
    data["process_to_achieve_outcomes"] = process_to_achieve_outcomes
    # Add the justifications, set to None if empty
    data["justifications"] = summary_justification if summary_justification else None

    return data


def human_agency_principle(data):
    human_agency_all_yes_wim = [
        """
    Company has put in place appropriate oversight and
    control measures so that human can intervene should AI
    system fail to achieve its intended goal and result in a
    negative outcome. This enables human to retain the
    ability to improve and override the operation of AI
    system.
    """
    ]
    human_agency_not_all_yes_wim = [
        """
    Company may not have put in place adequate oversight
    and control measures for human to intervene should AI
    system fail to achieve its intended goal and result in a
    negative outcome.
    <br/><br/>Without structured review processes, training, or
    accessible system documentation, decision-makers may
    struggle to identify red flags or weigh the downstream
    impact of deployment.
    <br/><br/>Systems with feedback loop or learning capabilities may
    also evolve beyond their original intent. Without regular
    evaluations or system-specific guardrails, risks may go
    undetected.
    <br/>This may result in increase in risk of harm to end users of
    or individuals affected by the AI system.
    """
    ]
    human_agency_recommendation = """
    Company should review the current oversight and control
    that spans development and deployment stages to ensure
    that human is able to improve the operation of AI system
    or override it in a timely manner when system fails.
    """

    process_to_achieve_outcomes = []
    summary_justification = []
    all_yes = True
    # Check the implementation status for the human agency & oversight principle
    for principle_id, processes in data["process_checks"].items():
        for process_id, details in processes.items():
            if details["principle_key"].strip() == "10. Human agency":
                if details["implementation"] != "Yes":
                    all_yes = False
                    process_to_achieve_outcomes.append(
                        details["process_to_achieve_outcomes"].replace("\n", "<br/>")
                    )
                    elaboration = details.get("elaboration", "").strip()
                    if elaboration:
                        summary_justification.append(elaboration)

    # Update the JSON with the appropriate description or WIM
    if all_yes:
        data["human_agency_description"] = ALL_YES_DESC
        data["human_agency_wim"] = human_agency_all_yes_wim
        data["human_agency_recommendation"] = ""
    else:
        data["human_agency_description"] = NOT_ALL_YES_DESC
        data["human_agency_wim"] = human_agency_not_all_yes_wim
        data["human_agency_recommendation"] = human_agency_recommendation

    # Append the outcome descriptions for "No" or "N/A"
    data["process_to_achieve_outcomes"] = process_to_achieve_outcomes

    # Add the justifications, set to None if empty
    data["justifications"] = summary_justification if summary_justification else None
    return data


def inc_growth_principle(data):
    inc_growth_soc_env_wellbeing_all_yes_wim = [
        """
    Company has considered the broader implications of the
    AI system, i.e., its impact on society and environment,
    beyond its functional and commercial objectives.
    """
    ]
    inc_growth_soc_env_wellbeing_not_all_yes_wim = [
        """
    Company may not be able to fully demonstrate that it has
    considered the broader implications of the AI system, i.e.,
    its impact on society and environment, beyond its
    functional and commercial objectives. Company may
    overlook ways to design systems that deliver long-term
    public value — such as accessibility improvements,
    sustainability gains, or socially aligned features.
    """
    ]
    inc_growth_soc_env_wellbeing_recommendation = """
    Stakeholders (e.g., regulators, partners, and consumers)
    increasingly scrutinise the social and environmental
    impact of AI. Company should review the reasons for not
    implementing certain processes and assess if these
    reasons are still valid. Company can consider assessing
    the potential societal and environmental benefits or harms
    — even if qualitative — during project scoping or
    approval stages
    """

    process_to_achieve_outcomes = []
    summary_justification = []
    all_yes = True

    # Check the implementation status for the inclusive growth, social & environmental wellbeing principle
    for principle_id, processes in data["process_checks"].items():
        for process_id, details in processes.items():
            if details["principle_key"].strip() == "11. Inclusive growth":
                if details["implementation"] != "Yes":
                    all_yes = False
                    process_to_achieve_outcomes.append(
                        details["process_to_achieve_outcomes"].replace("\n", "<br/>")
                    )
                    elaboration = details.get("elaboration", "").strip()
                    if elaboration:
                        summary_justification.append(elaboration)

    # Update the JSON with the appropriate description or WIM
    if all_yes:
        data["inc_growth_description"] = ALL_YES_DESC
        data["inc_growth_wim"] = inc_growth_soc_env_wellbeing_all_yes_wim
        data["inc_growth_recommendation"] = ""
    else:
        data["inc_growth_description"] = NOT_ALL_YES_DESC
        data["inc_growth_wim"] = inc_growth_soc_env_wellbeing_not_all_yes_wim
        data["inc_growth_recommendation"] = inc_growth_soc_env_wellbeing_recommendation

    # Append the outcome descriptions for "No" or "N/A"
    data["process_to_achieve_outcomes"] = process_to_achieve_outcomes

    # Add the justifications, set to None if empty
    data["justifications"] = summary_justification if summary_justification else None
    return data


def process_principle(data, principle_name, principle_number):
    """
    Processes the given principle data to compute implementation statistics and
    generate a summary output.

    This function evaluates the implementation status of processes associated
    with a specific principle, calculates the counts of "Yes", "No", and "N/A"
    implementations, and determines if all implementations are "Yes". It also
    retrieves additional information such as descriptions, recommendations, and
    justifications related to the principle.

    Args:
        data (dict): The data containing process checks and other related information.
        principle_name (str): The name of the principle to process.
        principle_number (int): The number associated with the principle.

    Returns:
        dict: A dictionary containing the processed data for the principle,
              including implementation counts, descriptions, recommendations,
              and justifications.
    """
    # Call the corresponding principle function
    formatted_principle_name = f"{principle_name.replace(' ', '_')}"
    principle_function = globals().get(f"{formatted_principle_name}_principle")
    if principle_function:
        data = principle_function(data)
    # Initialize a dictionary to hold the counts
    implementation_counts = defaultdict(lambda: {"Yes": 0, "No": 0, "N/A": 0})

    # Iterate over the process checks
    for principle_id, processes in data["process_checks"].items():
        for process_id, details in processes.items():
            principle_key = details["principle_key"].strip()
            implementation_status = details["implementation"]
            # Count the implementations
            if implementation_status in implementation_counts[principle_key]:
                implementation_counts[principle_key][implementation_status] += 1

    # Convert the defaultdict to a regular dictionary for JSON serialization
    implementation_counts = dict(implementation_counts)

    # Check if the principle name is "human agency" and adjust the principle key accordingly
    if principle_name == "human agency":
        principle_key = f"{principle_number}. Human agency"
    elif principle_name == "inc growth":
        principle_key = f"{principle_number}. Inclusive growth"
    else:
        principle_key = f"{principle_number}. {' '.join(word.capitalize() for word in principle_name.split())}"

    yes_count = implementation_counts.get(principle_key, {}).get("Yes", 0)
    no_count = implementation_counts.get(principle_key, {}).get("No", 0)
    na_count = implementation_counts.get(principle_key, {}).get("N/A", 0)

    # Add a key to indicate if all implementations are "Yes"
    all_yes = yes_count > 0 and no_count == 0 and na_count == 0
    output_data = {
        principle_name: {
            "yes": yes_count,
            "no": no_count,
            "na": na_count,
            "all_yes": all_yes,
            "description": data.get(f"{formatted_principle_name}_description", ""),
            "wim": data.get(f"{formatted_principle_name}_wim", []),
            "recommendation": data.get(
                f"{formatted_principle_name}_recommendation", ""
            ),
        },
        "process_to_achieve_outcomes": data.get("process_to_achieve_outcomes", []),
        "justifications": data.get("justifications", None),
    }
    return output_data
