#!/bin/bash

python_script=$1
json_file=$2

# Load the JSON file and extract the arguments and lists of values
arguments=()
values=()
while read -r key value; do
    case $key in
        "log_root")
            log_root=$value
            ;;
        "control_args")
            control_args=$(python3 -c "import json, sys; data = json.loads(sys.stdin.read()); print(json.dumps(data.get('control_args', {})))" < $json_file)
            ;;
        "hidden_args")
            hidden_args=$(python3 -c "import json, sys; data = json.loads(sys.stdin.read()); print(json.dumps(data.get('control_args', {})))" < $hidden_file)
            echo "$hidden_args"
            ;;
        *)
            arguments+=("$key")
            values+=("$value")
            ;;
    esac
done < <(jq -r 'to_entries | .[] | "\(.key) \(.value | join(","))"' $json_file)

hidden_keys=()
hidden_values=()
while read -r key value; do
    hidden_keys+=("$key")
    hidden_values+=("$value")
done < <(jq -r 'to_entries | .[] | "\(.key) \(.value)"' $hidden_args)

# Generate all possible combinations of the argument / value pairs
combinations=()
for i in "${!arguments[@]}"; do
    if [[ -z "${combinations[@]}" ]]; then
        for val in $(echo "${values[$i]}" | tr ',' '\n'); do
            combinations+=("$(echo "--${arguments[$i]}=$val")")
        done
    else
        new_combinations=()
        for c in "${combinations[@]}"; do
            for val in $(echo "${values[$i]}" | tr ',' '\n'); do
                new_combinations+=("$c $(echo "--${arguments[$i]}=$val")")
            done
        done
        combinations=("${new_combinations[@]}")
    fi
done

# Generate all possible combinations of the argument / value pairs
hidden_combinations=()

# Generate additional arguments from control_args dictionary
control_args_args=()
for key in $(echo "$control_args" | jq -r 'keys[]'); do
    value=$(echo "$control_args" | jq -r ".$key")
    control_args_args+=("--$key=$value")
done

# Combine control_args_args with each combination of argument / value pairs
final_combinations=()
for c in "${combinations[@]}"; do
    for control_arg_arg in "${control_args_args[@]}"; do
        final_combinations+=("$c $control_arg_arg")
    done
done

# Run the Python script with each combination of argument / value pairs
# for c in "${final_combinations[@]}"; do
#     python3 $python_script $c
if ${#combinations[@]} -gt 0; then
    for c in "${combinations[@]}"; do
        log_dir="$log_root"
        arg_str=""
        for arg in $c; do
            arg_str+=" $arg"
            arg_name=${arg:2}
            log_dir="$log_dir/$arg_name"
        done

        if ${#hidden_combinations[@]} -gt 0; then
            for h in "${hidden_combinations[@]}"; do

                for arg in $h; do
                    arg_str+=" $arg"
                done

                for arg in "${control_args_args[@]}"; do
                    arg_str+=" $arg"
                done

                mkdir -p "$log_dir"

                arg_str+=" --log_dir=$log_dir"
                echo $arg_str
                python "$python_script" $arg_str
            done
        else
            for arg in "${control_args_args[@]}"; do
                arg_str+=" $arg"
            done

            mkdir -p "$log_dir"

            arg_str+=" --log_dir=$log_dir"
            echo $arg_str
            python "$python_script" $arg_str
        fi
    done
else
    for h in "${hidden_combinations[@]}"; do
        log_dir="$log_root"
        arg_str=""
        for arg in $h; do
            arg_str+=" $arg"
        done

        for arg in "${control_args_args[@]}"; do
            arg_str+=" $arg"
        done

        mkdir -p "$log_dir"

        arg_str+=" --log_dir=$log_dir"
        echo $arg_str
        python "$python_script" $arg_str
    done
fi